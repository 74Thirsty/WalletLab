# Copyright 2026 CE Hirschauer

import tkinter as tk
from tkinter import simpledialog, messagebox, scrolledtext

try:
    from bip_utils import (
        Bip39MnemonicGenerator,
        Bip39SeedGenerator,
        Bip44,
        Bip44Coins,
        Bip44Changes,
        Bip32Slip10Secp256k1,
    )
except ImportError:
    raise SystemExit(
        "Missing dependency: bip_utils\n"
        "Install it with: pip install bip-utils"
    )


APP_TITLE = (
    "mm     mm                                            mm        \n"
    "*@@@@*     @     *@@@*          *@@@   *@@@             @@        *@@@@*              m@@        \n"
    "  *@@     m@@     m@              @@     @@             @@          @@                 @@        \n"
    "   @@m   m@@@m   m@    m@*@@m     @@     @@    mm@*@@ @@@@@@        @@       m@*@@m    @@m@@@@m  \n"
    "    @@m  @* @@m  @*   @@   @@     !@     !@   m@*   @@  @@          @@      @@   @@    @@    *@@ \n"
    "    !@@ @*  *@@ @*     m@@@!@     !@     !@   !@******  @@          @!     m m@@@!@    !@     @@ \n"
    "     !@@m    !@@m     @!   !@     !@     !@   !@m    m  @!          @!    :@@!   !@    !!!   m@! \n"
    "     !!@!*   !!@!*     !!!!:!     !!     !!   !!******  !!          !!     ! !!!!:!    !!     !! \n"
    "     !!!!    !!!!     !!   :!     :!     :!   :!!       !!          !:    !!!!   :!    :!!   !!! \n"
    "      :       :       :!: : !:  : : :  : : :   : : ::   ::: :     : :: !: : :!: : !:   : : : ::  "
)


COIN_MAP = {
    "Bitcoin": Bip44Coins.BITCOIN,
    "Ethereum": Bip44Coins.ETHEREUM,
}


DEFAULT_PATHS = {
    "Bitcoin": "m/44'/0'/0'/0/0",
    "Ethereum": "m/44'/60'/0'/0/0",
}


class WalletGeneratorApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title(APP_TITLE)
        self.root.geometry("880x620")
        self.root.minsize(760, 520)

        self.output = scrolledtext.ScrolledText(root, wrap=tk.WORD, font=("Courier New", 10))
        self.output.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)

        btn_frame = tk.Frame(root)
        btn_frame.pack(fill=tk.X, padx=12, pady=(0, 12))

        tk.Button(btn_frame, text="Generate Wallet", command=self.generate_wallet, width=18).pack(side=tk.LEFT)
        tk.Button(btn_frame, text="Clear", command=self.clear_output, width=12).pack(side=tk.LEFT, padx=(8, 0))
        tk.Button(btn_frame, text="Copy Output", command=self.copy_output, width=12).pack(side=tk.LEFT, padx=(8, 0))
        tk.Button(btn_frame, text="Exit", command=root.destroy, width=12).pack(side=tk.RIGHT)

        self.write_intro()

    def write_intro(self):
        intro = (
            "HD Wallet Generator\n"
            "=" * 72 + "\n"
            "This tool creates a mnemonic seed, seed hex, private key, public key, and\n"
            "address using a popup-driven flow. Keep it offline and protect the output.\n\n"
            "Supported coins: Bitcoin, Ethereum\n"
            "Default derivation paths:\n"
            "  Bitcoin  -> m/44'/0'/0'/0/0\n"
            "  Ethereum -> m/44'/60'/0'/0/0\n\n"
            "Click 'Generate Wallet' to begin.\n"
        )
        self.output.insert(tk.END, intro)
        self.output.see(tk.END)

    def clear_output(self):
        self.output.delete("1.0", tk.END)

    def copy_output(self):
        text = self.output.get("1.0", tk.END).strip()
        if not text:
            messagebox.showinfo(APP_TITLE, "There is no output to copy yet.")
            return
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        self.root.update()
        messagebox.showinfo(APP_TITLE, "Output copied to clipboard.")

    def ask_coin(self) -> str | None:
        prompt = (
            "Choose a coin:\n\n"
            "1 = Bitcoin\n"
            "2 = Ethereum"
        )
        choice = simpledialog.askstring(APP_TITLE, prompt, parent=self.root)
        if choice is None:
            return None

        choice = choice.strip().lower()
        if choice in {"1", "bitcoin", "btc"}:
            return "Bitcoin"
        if choice in {"2", "ethereum", "eth"}:
            return "Ethereum"

        messagebox.showerror(APP_TITLE, "Invalid coin choice.")
        return self.ask_coin()

    def ask_word_count(self) -> int | None:
        prompt = "Enter mnemonic length: 12, 15, 18, 21, or 24"
        value = simpledialog.askinteger(APP_TITLE, prompt, parent=self.root, minvalue=12, maxvalue=24)
        if value is None:
            return None
        if value not in {12, 15, 18, 21, 24}:
            messagebox.showerror(APP_TITLE, "Word count must be one of: 12, 15, 18, 21, 24.")
            return self.ask_word_count()
        return value

    def ask_yes_no(self, prompt: str) -> bool | None:
        result = messagebox.askyesnocancel(APP_TITLE, prompt, parent=self.root)
        if result is None:
            return None
        return bool(result)

    def ask_custom_path(self, coin_name: str) -> str | None:
        default_path = DEFAULT_PATHS[coin_name]
        use_custom = self.ask_yes_no(
            f"Use a custom derivation path?\n\nDefault for {coin_name}:\n{default_path}"
        )
        if use_custom is None:
            return None
        if not use_custom:
            return default_path

        path = simpledialog.askstring(
            APP_TITLE,
            f"Enter derivation path for {coin_name}:\nExample: {default_path}",
            initialvalue=default_path,
            parent=self.root,
        )
        if path is None:
            return None
        path = path.strip()
        if not path.startswith("m/"):
            messagebox.showerror(APP_TITLE, "Derivation path must start with 'm/'.")
            return self.ask_custom_path(coin_name)
        return path

    def ask_passphrase(self) -> str | None:
        return simpledialog.askstring(
            APP_TITLE,
            "Optional BIP39 passphrase (leave blank for none):",
            show="*",
            parent=self.root,
        )

    def derive_with_standard_bip44(self, seed_bytes: bytes, coin_name: str):
        wallet = (
            Bip44.FromSeed(seed_bytes, COIN_MAP[coin_name])
            .Purpose()
            .Coin()
            .Account(0)
            .Change(Bip44Changes.CHAIN_EXT)
            .AddressIndex(0)
        )
        return {
            "private_key_hex": wallet.PrivateKey().Raw().ToHex(),
            "public_key_hex": wallet.PublicKey().RawCompressed().ToHex(),
            "address": wallet.PublicKey().ToAddress(),
        }

    def derive_with_custom_path(self, seed_bytes: bytes, path: str, coin_name: str):
        ctx = Bip32Slip10Secp256k1.FromSeed(seed_bytes)
        node = ctx.DerivePath(path.replace("m/", ""))

        pub_hex = node.PublicKey().RawCompressed().ToHex()
        priv_hex = node.PrivateKey().Raw().ToHex()

        # Address generation on custom paths is not universal across coins.
        # We keep it simple and show address only when path matches the standard one.
        address = "Custom path selected; address display omitted for safety/compatibility."
        if path == DEFAULT_PATHS[coin_name]:
            std = self.derive_with_standard_bip44(seed_bytes, coin_name)
            address = std["address"]

        return {
            "private_key_hex": priv_hex,
            "public_key_hex": pub_hex,
            "address": address,
        }

    def generate_wallet(self):
        try:
            coin_name = self.ask_coin()
            if coin_name is None:
                return

            word_count = self.ask_word_count()
            if word_count is None:
                return

            path = self.ask_custom_path(coin_name)
            if path is None:
                return

            passphrase = self.ask_passphrase()
            if passphrase is None:
                return
            passphrase = passphrase or ""

            mnemonic = Bip39MnemonicGenerator().FromWordsNumber(word_count)
            seed_bytes = Bip39SeedGenerator(str(mnemonic)).Generate(passphrase)
            seed_hex = seed_bytes.hex()

            if path == DEFAULT_PATHS[coin_name]:
                derived = self.derive_with_standard_bip44(seed_bytes, coin_name)
            else:
                derived = self.derive_with_custom_path(seed_bytes, path, coin_name)

            result = (
                "\n" + "=" * 72 + "\n"
                f"Coin              : {coin_name}\n"
                f"Mnemonic words    : {word_count}\n"
                f"Derivation path   : {path}\n"
                f"BIP39 passphrase  : {'<set>' if passphrase else '<none>'}\n"
                f"Mnemonic          : {mnemonic}\n"
                f"Seed hex          : {seed_hex}\n"
                f"Private key hex   : {derived['private_key_hex']}\n"
                f"Public key hex    : {derived['public_key_hex']}\n"
                f"Address           : {derived['address']}\n"
            )

            self.output.insert(tk.END, result)
            self.output.see(tk.END)
            messagebox.showinfo(APP_TITLE, "Wallet generated successfully.")

        except Exception as exc:
            messagebox.showerror(APP_TITLE, f"Error: {exc}")


class SplashScreen:
    def __init__(self, root: tk.Tk, duration_ms: int = 3000):
        self.root = root
        self.root.withdraw()

        self.splash = tk.Toplevel(root)
        self.splash.overrideredirect(True)

        display = APP_TITLE + "\n\n  Copyright 2026 CE Hirschauer\n\n  Click or press any key to continue"

        label = tk.Label(
            self.splash,
            text=display,
            font=("Courier New", 10),
            justify=tk.LEFT,
            bg="black",
            fg="lime",
            padx=20,
            pady=20,
        )
        label.pack()

        self.splash.update_idletasks()
        w = self.splash.winfo_reqwidth()
        h = self.splash.winfo_reqheight()
        x = (self.splash.winfo_screenwidth() // 2) - (w // 2)
        y = (self.splash.winfo_screenheight() // 2) - (h // 2)
        self.splash.geometry(f"+{x}+{y}")

        self.splash.bind("<Button-1>", lambda e: self.dismiss())
        self.splash.bind("<Key>", lambda e: self.dismiss())
        self.splash.focus_set()
        self.splash.after(duration_ms, self.dismiss)

    def dismiss(self):
        try:
            self.splash.destroy()
        except tk.TclError:
            pass
        self.root.deiconify()


if __name__ == "__main__":
    root = tk.Tk()
    SplashScreen(root)
    app = WalletGeneratorApp(root)
    root.mainloop()
