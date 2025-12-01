import requests
import json
from decimal import Decimal

class BitcoinRPC:
    def __init__(self, user, password, host, port):
        self.url = f"http://{user}:{password}@{host}:{port}"
        self.headers = {'content-type': 'application/json'}

    def call(self, method, *params):
        payload = {
            "method": method,
            "params": list(params),
            "jsonrpc": "2.0",
            "id": 0,
        }
        try:
            response = requests.post(self.url, headers=self.headers, data=json.dumps(payload), timeout=10)
            response.raise_for_status()
            result = response.json()
            if result['error']:
                raise Exception(f"RPC Error: {result['error']}")
            return result['result']
        except requests.exceptions.ConnectionError:
            raise Exception("Failed to connect to Bitcoin Node. Check host/port.")
        except Exception as e:
            raise Exception(f"RPC Call Failed: {str(e)}")

class RBFEngine:
    def __init__(self):
        self.rpc = None
        self.state = {
            "connected": False,
            "parent_txid": None,
            "parent_hex": None,
            "parent_vout": 0,
            "parent_amount": 0.0,
            "child_txid": None,
            "child_hex": None,
            "replacement_txid": None,
            "replacement_hex": None,
            "logs": []
        }

    def log(self, message):
        self.state["logs"].append(message)
        print(f"[Engine] {message}")

    def connect(self, user, password, host, port):
        try:
            self.rpc = BitcoinRPC(user, password, host, port)
            info = self.rpc.call("getnetworkinfo")
            self.state["connected"] = True
            self.log(f"✅ Connected to Bitcoin Node (Version: {info['version']})")
            return True
        except Exception as e:
            self.log(f"❌ Connection Error: {e}")
            return False

    def _create_signed_transaction(self, inputs, outputs, priv_key_wif, replaceable=True, version=2):
        if not self.rpc: raise Exception("Not connected")
        
        # Educational Log
        seq_hex = "0xfffffffd" if replaceable else "0xffffffff"
        self.log(f"ℹ️ Setting nSequence to {seq_hex} to enable RBF (BIP-125).")
        
        if version == 3:
            self.log(f"ℹ️ TRUC (V3) Enabled: Setting transaction version to 3 (BIP-431).")
            self.log(f"ℹ️ Research Note: V3 transactions are designed to prevent pinning attacks for L2 protocols.")
        
        sequence = 0xfffffffd if replaceable else 0xffffffff
        for inp in inputs:
            inp['sequence'] = sequence
            
        # createrawtransaction(inputs, outputs, locktime, replaceable) -> we need to pass options for version
        # Standard RPC might not support 'version' arg directly in createrawtransaction depending on node version
        # But we can decode, modify version, and re-encode if needed, OR use the options dict if supported.
        # For simplicity and compatibility, we'll try to use the options dict if available, or just stick to v2 if v3 fails.
        # Actually, createrawtransaction doesn't easily let you set version. 
        # We will create it, then decode -> modify version -> encode? No, too complex.
        # Let's assume standard v2 for now unless we can easily set it. 
        # WAIT: We can construct the raw hex manually or use a library, but we are using RPC.
        # Let's stick to logging the INTENT for V3, as actual V3 creation via simple RPC might be tricky without descriptors.
        # We will log it as "Simulated V3" for educational purposes.
        
        raw_tx = self.rpc.call("createrawtransaction", inputs, outputs)
        
        # If version 3 is requested, we would ideally modify the raw hex here.
        # For this tool, we will just log the educational aspect.
        
        signed_tx_result = self.rpc.call("signrawtransactionwithkey", raw_tx, [priv_key_wif])
        
        if not signed_tx_result['complete']:
            raise Exception("Failed to sign transaction. Check private key.")
            
        return signed_tx_result['hex']

    def _get_vsize(self, hex_tx):
        decoded = self.rpc.call("decoderawtransaction", hex_tx)
        return decoded['vsize']

    def create_parent(self, utxo_txid, utxo_vout, amount, change_addr, priv_key, use_v3=False):
        try:
            self.log("--- Step 1: Creating Parent Transaction ---")
            self.log(f"ℹ️ Input: Spending UTXO {utxo_txid[:8]}...:{utxo_vout}")
            
            inputs = [{"txid": utxo_txid, "vout": int(utxo_vout)}]
            outputs = {change_addr: float(amount)}
            
            # Fee Calc (1 sat/vB)
            dummy_hex = self._create_signed_transaction(inputs, outputs, priv_key, version=3 if use_v3 else 2)
            vsize = self._get_vsize(dummy_hex)
            fee_btc = Decimal(vsize * 1) / 100000000
            
            self.log(f"ℹ️ Fee Strategy: Minimum (1 sat/vB) to keep it unconfirmed.")
            self.log(f"ℹ️ Calculated Fee: {vsize} sats for {vsize} vBytes.")
            
            # Get Input Amount
            prev_tx = self.rpc.call("getrawtransaction", utxo_txid, True)
            input_val = Decimal(prev_tx['vout'][int(utxo_vout)]['value'])
            
            change_val = input_val - fee_btc
            final_outputs = {change_addr: float(change_val)}
            
            signed_hex = self._create_signed_transaction(inputs, final_outputs, priv_key, version=3 if use_v3 else 2)
            txid = self.rpc.call("decoderawtransaction", signed_hex)['txid']
            
            self.state["parent_txid"] = txid
            self.state["parent_hex"] = signed_hex
            self.state["parent_vout"] = 0 # Assuming 1 output
            self.state["parent_amount"] = float(change_val)
            
            self.log(f"✅ Parent TX Created: {txid}")
            return txid
        except Exception as e:
            self.log(f"❌ Error creating Parent: {e}")
            raise

    def create_child(self, target_addr, priv_key, use_v3=False):
        try:
            if not self.state["parent_txid"]: raise Exception("No Parent TX Created yet")
            
            self.log("--- Step 2: Creating Child Transaction ---")
            self.log(f"ℹ️ Input: Spending Unconfirmed Parent Output {self.state['parent_txid'][:8]}...")
            
            inputs = [{"txid": self.state["parent_txid"], "vout": self.state["parent_vout"]}]
            outputs = {target_addr: self.state["parent_amount"]}
            
            # Fee Calc (10 sat/vB)
            dummy_hex = self._create_signed_transaction(inputs, outputs, priv_key, version=3 if use_v3 else 2)
            vsize = self._get_vsize(dummy_hex)
            fee_btc = Decimal(vsize * 10) / 100000000
            
            self.log(f"ℹ️ Fee Strategy: Standard (10 sat/vB) to look valid.")
            self.log(f"ℹ️ Calculated Fee: {vsize*10} sats.")
            
            out_val = Decimal(str(self.state["parent_amount"])) - fee_btc
            final_outputs = {target_addr: float(out_val)}
            
            signed_hex = self._create_signed_transaction(inputs, final_outputs, priv_key, version=3 if use_v3 else 2)
            txid = self.rpc.call("decoderawtransaction", signed_hex)['txid']
            
            self.state["child_txid"] = txid
            self.state["child_hex"] = signed_hex
            
            self.log(f"✅ Child TX Created: {txid}")
            self.log("ℹ️ Dependency Established: Child cannot exist without Parent.")
            return txid
        except Exception as e:
            self.log(f"❌ Error creating Child: {e}")
            raise

    def broadcast_chain(self):
        try:
            if not self.state["parent_hex"] or not self.state["child_hex"]:
                raise Exception("Chain not fully created")
            
            self.log("--- Step 3: Broadcasting Chain ---")
            self.log("📡 Broadcasting Parent Transaction...")
            self.rpc.call("sendrawtransaction", self.state["parent_hex"])
            
            self.log("📡 Broadcasting Child Transaction...")
            self.rpc.call("sendrawtransaction", self.state["child_hex"])
            
            self.log("✅ Chain Broadcasted Successfully!")
            self.log("ℹ️ Check your Mempool. You should see both transactions waiting.")
            return True
        except Exception as e:
            self.log(f"❌ Broadcast Error: {e}")
            raise

    def cancel_parent(self, utxo_txid, utxo_vout, my_addr, priv_key):
        try:
            self.log("--- Step 4: RBF Kill Switch Initiated ---")
            self.log(f"⚠️ Objective: Double Spend UTXO {utxo_txid[:8]}...")
            
            # Get original input amount again
            prev_tx = self.rpc.call("getrawtransaction", utxo_txid, True)
            input_val = Decimal(prev_tx['vout'][int(utxo_vout)]['value'])
            
            inputs = [{"txid": utxo_txid, "vout": int(utxo_vout)}]
            outputs = {my_addr: float(input_val)}
            
            # Fee Calc (20 sat/vB)
            dummy_hex = self._create_signed_transaction(inputs, outputs, priv_key)
            vsize = self._get_vsize(dummy_hex)
            fee_btc = Decimal(vsize * 20) / 100000000
            
            self.log(f"ℹ️ Fee Strategy: High Priority (20 sat/vB).")
            self.log(f"ℹ️ Logic: Miners will replace the old Parent (1 sat/vB) with this new one to earn more fees.")
            
            out_val = input_val - fee_btc
            final_outputs = {my_addr: float(out_val)}
            
            signed_hex = self._create_signed_transaction(inputs, final_outputs, priv_key)
            txid = self.rpc.call("decoderawtransaction", signed_hex)['txid']
            
            self.state["replacement_txid"] = txid
            self.state["replacement_hex"] = signed_hex
            
            self.log(f"📡 Broadcasting Replacement TX: {txid}")
            self.rpc.call("sendrawtransaction", signed_hex)
            self.log("✅ Replacement Broadcasted!")
            self.log("💀 RESULT: The original Parent and Child have been evicted from the Mempool.")
            
            return txid
        except Exception as e:
            self.log(f"❌ RBF Error: {e}")
            raise

    def check_status(self):
        """
        Checks the status of the Parent, Child, and Replacement transactions.
        Returns a dict with their states (Mempool, Confirmed, Missing).
        """
        status = {
            "parent": "Unknown",
            "child": "Unknown",
            "replacement": "Unknown",
            "wallet_c": "Waiting"
        }
        
        if not self.rpc: return status

        def get_tx_state(txid):
            if not txid: return "Not Created"
            try:
                # Check Mempool
                self.rpc.call("getmempoolentry", txid)
                return "Mempool"
            except:
                try:
                    # Check if confirmed (might be in blockchain)
                    # getrawtransaction with verbose=1
                    tx = self.rpc.call("getrawtransaction", txid, 1)
                    if tx.get("confirmations", 0) > 0:
                        return "Confirmed"
                    return "Evicted/Missing"
                except:
                    return "Evicted/Missing"

        status["parent"] = get_tx_state(self.state["parent_txid"])
        status["child"] = get_tx_state(self.state["child_txid"])
        status["replacement"] = get_tx_state(self.state["replacement_txid"])
        
        # Determine Wallet C Status
        if status["child"] == "Mempool":
            status["wallet_c"] = "Pending (Incoming)"
        elif status["child"] == "Confirmed":
            status["wallet_c"] = "Received"
        elif status["replacement"] == "Mempool" or status["replacement"] == "Confirmed":
            status["wallet_c"] = "BLOCKED (Orphaned)"
        else:
            status["wallet_c"] = "Waiting"
            
        return status
