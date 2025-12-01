# RBF & Mempool Ancestry Visualizer

A powerful, educational tool designed to visualize and experiment with **Replace-By-Fee (RBF)**, **Mempool Ancestry**, and **Double Spend** dynamics on the Bitcoin Testnet.

![RBF Visualizer Interface](https://via.placeholder.com/800x400?text=RBF+Visualizer+Interface)

## 🚀 Features

-   **Interactive Visualization**: See the relationship between Parent and Child transactions in real-time.
-   **RBF "Kill Switch"**: Execute a Double Spend attack to invalidate a chain of unconfirmed transactions.
-   **V3 Transaction Support**: Experiment with BIP-431 (TRUC) transactions (simulated/educational).
-   **Multi-Language Support**: Switch seamlessly between English (EN) and Arabic (AR).
-   **Real-Time Logs**: Detailed, educational logs explaining every step of the process.
-   **Modern UI**: A sleek, "Glassmorphism" design for a premium user experience.

## 🛠️ Prerequisites

-   **Python 3.7+**
-   **Bitcoin Core Node**: You need access to a Bitcoin Core node running on **Testnet** or **Regtest**.
    -   *Note: This tool requires RPC access to the node.*

## 📦 Installation

1.  **Clone the Repository**
    ```bash
    git clone https://github.com/yourusername/rbf-visualizer.git
    cd rbf-visualizer
    ```

2.  **Install Dependencies**
    ```bash
    pip install flask requests
    ```

## 🚦 Usage

1.  **Start the Application**
    ```bash
    python app.py
    ```
    The app will run at `http://127.0.0.1:5000`.

2.  **Connect to Node**
    -   Open the web interface.
    -   Enter your Bitcoin Node's **RPC Credentials** (User, Password, Host, Port).
    -   Click **Connect**.

3.  **Setup Wallet**
    -   **Private Key (WIF)**: Enter the WIF private key for the wallet that owns the UTXO.
    -   **UTXO TXID & VOUT**: Enter the Transaction ID and Output Index of a confirmed UTXO you want to spend.
    -   **Addresses**:
        -   *Change Address (Wallet B)*: Where the change from the Parent TX goes.
        -   *Target Address (Wallet C)*: Where the Child TX sends funds.

4.  **Run the Experiment**
    -   **Step 1: Create Parent**: Creates a low-fee (1 sat/vB) transaction.
    -   **Step 2: Create Child**: Creates a high-fee (10 sat/vB) transaction spending the Parent's output (CPFP).
    -   **Step 3: Broadcast**: Sends both to the network.
    -   **🛑 STOP ALL**: Sends a high-fee (20 sat/vB) Replacement Transaction that double-spends the original UTXO, effectively "killing" the Parent and Child.

## 📂 Project Structure

-   `app.py`: Flask backend server handling API requests.
-   `rbf_engine.py`: Core logic for Bitcoin RPC interaction and transaction creation.
-   `templates/index.html`: The main frontend interface.
-   `static/style.css`: Styling and animations.

## ⚠️ Disclaimer

**EDUCATIONAL PURPOSES ONLY.**
This tool is designed for **Testnet** or **Regtest** environments.
**DO NOT USE ON MAINNET.**
Using this tool on Mainnet with real funds may result in **loss of funds** due to transaction fees or mistakes. The authors are not responsible for any financial loss.

---
*Built with ❤️ for Bitcoin Education.*
