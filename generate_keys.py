import json
import random
import string
from datetime import datetime, timedelta

class KeyGenerator:
    def __init__(self, db_file='keys.json'):
        self.db_file = db_file
        self.load_database()
    
    def load_database(self):
        try:
            with open(self.db_file, 'r') as f:
                self.data = json.load(f)
        except:
            self.data = {"database": {}, "banned_hwids": [], "settings": {"max_devices_per_key": 1, "allow_reset": True}}
    
    def save_database(self):
        with open(self.db_file, 'w') as f:
            json.dump(self.data, f, indent=4)
        print(f"✅ Database saved to {self.db_file}")
    
    def generate_key(self, prefix="DJTEAM", length=16, separator="-"):
        """Generate random key: DJTEAM-XXXX-XXXX-XXXX"""
        chars = string.ascii_uppercase + string.digits
        key_body = ''.join(random.choices(chars, k=length))
        
        # Format dengan separator setiap 4 karakter
        if separator:
            parts = [key_body[i:i+4] for i in range(0, length, 4)]
            key = prefix + separator + separator.join(parts)
        else:
            key = prefix + key_body
        
        return key
    
    def add_key(self, owner="anonymous", days_valid=365, custom_key=None):
        """Tambah key baru ke database"""
        key = custom_key if custom_key else self.generate_key()
        
        # Cek duplikat
        if key in self.data["database"]:
            print(f"❌ Key {key} sudah ada!")
            return None
        
        created = datetime.now()
        expires = created + timedelta(days=days_valid) if days_valid else None
        
        self.data["database"][key] = {
            "status": "active",
            "hwid": None,
            "used": False,
            "created": created.strftime("%Y-%m-%d"),
            "expires": expires.strftime("%Y-%m-%d") if expires else None,
            "owner": owner,
            "device_name": None,
            "first_use": None,
            "last_check": None
        }
        
        self.save_database()
        print(f"✅ Key generated: {key}")
        print(f"   Owner: {owner}")
        print(f"   Valid until: {expires.strftime('%Y-%m-%d') if expires else 'Lifetime'}")
        return key
    
    def list_keys(self, show_all=False):
        """Tampilkan semua key"""
        print("\n" + "="*60)
        print("DJTEAM KEY DATABASE")
        print("="*60)
        
        for key, info in self.data["database"].items():
            status_icon = "🟢" if info["status"] == "active" else "🔴"
            used_icon = "✅" if info["used"] else "⬜"
            
            if show_all or info["status"] == "active":
                print(f"{status_icon} {used_icon} {key}")
                print(f"   Owner: {info['owner']}")
                print(f"   HWID: {info['hwid'][:20] + '...' if info['hwid'] else 'Not bound'}")
                print(f"   Expires: {info['expires'] or 'Never'}")
                print("-" * 60)
    
    def reset_hwid(self, key):
        """Reset HWID binding (unbind device)"""
        if key not in self.data["database"]:
            print(f"❌ Key {key} tidak ditemukan!")
            return False
        
        old_hwid = self.data["database"][key]["hwid"]
        self.data["database"][key]["hwid"] = None
        self.data["database"][key]["used"] = False
        self.data["database"][key]["device_name"] = None
        
        self.save_database()
        print(f"✅ HWID reset untuk key: {key}")
        print(f"   HWID lama: {old_hwid}")
        return True
    
    def ban_hwid(self, hwid, reason=""):
        """Ban HWID tertentu"""
        if hwid not in self.data["banned_hwids"]:
            self.data["banned_hwids"].append({
                "hwid": hwid,
                "reason": reason,
                "banned_date": datetime.now().strftime("%Y-%m-%d")
            })
            self.save_database()
            print(f"🚫 HWID banned: {hwid}")
    
    def check_key(self, key, hwid=None):
        """Cek status key (untuk debugging)"""
        if key not in self.data["database"]:
            return {"valid": False, "message": "Key tidak ditemukan"}
        
        info = self.data["database"][key]
        
        if info["status"] != "active":
            return {"valid": False, "message": "Key tidak aktif"}
        
        if info["expires"]:
            if datetime.now() > datetime.strptime(info["expires"], "%Y-%m-%d"):
                return {"valid": False, "message": "Key expired"}
        
        # Cek banned HWID
        banned_list = [b["hwid"] for b in self.data["banned_hwids"]]
        if hwid and hwid in banned_list:
            return {"valid": False, "message": "Device banned"}
        
        # Cek binding
        if info["used"] and info["hwid"]:
            if hwid and info["hwid"] != hwid:
                return {"valid": False, "message": "Key sudah terbinding ke device lain"}
        
        return {"valid": True, "message": "Key valid"}

# ============================================
# CONSOLE MENU
# ============================================

def main():
    gen = KeyGenerator()
    
    while True:
        print("\n" + "="*40)
        print("DJTEAM KEY MANAGER")
        print("="*40)
        print("1. Generate Key Baru")
        print("2. Generate Multiple Keys")
        print("3. List Semua Key")
        print("4. Reset HWID (Unbind Device)")
        print("5. Ban HWID")
        print("6. Cek Status Key")
        print("7. Delete Key")
        print("0. Exit")
        
        choice = input("\nPilih menu: ")
        
        if choice == "1":
            owner = input("Nama pemilik: ") or "anonymous"
            days = int(input("Valid berapa hari (0=lifetime): ") or 365)
            custom = input("Custom key (kosongkan untuk random): ").strip() or None
            gen.add_key(owner, days, custom)
            
        elif choice == "2":
            count = int(input("Jumlah key: ") or 5)
            owner = input("Nama pemilik: ") or "anonymous"
            days = int(input("Valid berapa hari: ") or 365)
            
            keys = []
            for i in range(count):
                key = gen.add_key(owner, days)
                if key:
                    keys.append(key)
            
            print(f"\n✅ Generated {len(keys)} keys:")
            for k in keys:
                print(f"   {k}")
                
        elif choice == "3":
            show_all = input("Tampilkan key expired juga? (y/n): ").lower() == 'y'
            gen.list_keys(show_all)
            
        elif choice == "4":
            key = input("Masukkan key yang mau di-reset: ").strip()
            gen.reset_hwid(key)
            
        elif choice == "5":
            hwid = input("Masukkan HWID: ").strip()
            reason = input("Alasan ban: ")
            gen.ban_hwid(hwid, reason)
            
        elif choice == "6":
            key = input("Masukkan key: ").strip()
            hwid = input("Masukkan HWID (opsional): ").strip() or None
            result = gen.check_key(key, hwid)
            print(f"\nStatus: {result['message']}")
            
        elif choice == "7":
            key = input("Masukkan key yang mau dihapus: ").strip()
            if key in gen.data["database"]:
                del gen.data["database"][key]
                gen.save_database()
                print(f"✅ Key {key} dihapus")
            else:
                print("❌ Key tidak ditemukan")
                
        elif choice == "0":
            break

if __name__ == "__main__":
    main()
