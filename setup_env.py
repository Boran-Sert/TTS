import os
import subprocess
import sys
import urllib.request

def get_current_branch():
    try:
        branch = subprocess.check_output("git branch --show-current", shell=True, stderr=subprocess.DEVNULL).decode().strip()
        return branch if branch else "main"
    except Exception:
        return "main"

def run_command(command, description):
    print(f"\n[*] {description}...")
    try:
        subprocess.check_call(command, shell=True)
        print(f"[+] {description} tamamlandı.")
    except subprocess.CalledProcessError as e:
        print(f"[-] Hata oluştu: {description}")
        print(f"Hata kodu: {e.returncode}")
        sys.exit(1)

def check_and_download_trendyol_tts():
    print("\n[*] Trendyol-TTS model ağırlıkları kontrol ediliyor...")
    model_dir = "Trendyol_TTS"
    safetensors_path = os.path.join(model_dir, "model.safetensors")
    pth_path = os.path.join(model_dir, "audiovae.pth")
    
    if os.path.isfile(safetensors_path) and os.path.isfile(pth_path):
        print("[+] Trendyol-TTS model ağırlıkları halihazırda mevcut.")
    else:
        print("[-] Trendyol-TTS model ağırlıkları eksik. Hugging Face'ten indiriliyor...")
        try:
            from huggingface_hub import snapshot_download
            snapshot_download(
                repo_id="Trendyol/Trendyol-TTS",
                local_dir=model_dir,
                local_dir_use_symlinks=False
            )
            print("[+] Trendyol-TTS modeli başarıyla indirildi.")
        except Exception as e:
            print(f"[-] Trendyol-TTS modeli indirilirken hata oluştu: {e}")
            sys.exit(1)

def check_and_download_piper_model():
    print("\n[*] Piper-TTS model dosyaları kontrol ediliyor...")
    model_dir = "Piper-TTS-Model"
    onnx_path = os.path.join(model_dir, "model.onnx")
    json_path = os.path.join(model_dir, "config.json")
    
    os.makedirs(model_dir, exist_ok=True)
    
    onnx_url = "https://huggingface.co/rhasspy/piper-voices/resolve/main/tr/tr_TR/dfki/medium/tr_TR-dfki-medium.onnx"
    json_url = "https://huggingface.co/rhasspy/piper-voices/resolve/main/tr/tr_TR/dfki/medium/tr_TR-dfki-medium.onnx.json"
    
    if os.path.isfile(onnx_path) and os.path.isfile(json_path):
        print("[+] Piper-TTS model dosyaları halihazırda mevcut.")
    else:
        print("[-] Piper-TTS model dosyaları eksik. İndiriliyor...")
        try:
            if not os.path.isfile(onnx_path):
                print(f"    -> İndiriliyor: {onnx_path}")
                urllib.request.urlretrieve(onnx_url, onnx_path)
            
            if not os.path.isfile(json_path):
                print(f"    -> İndiriliyor: {json_path}")
                urllib.request.urlretrieve(json_url, json_path)
                
            print("[+] Piper-TTS modeli başarıyla indirildi.")
        except Exception as e:
            print(f"[-] Piper-TTS modeli indirilirken hata oluştu: {e}")
            sys.exit(1)

def main():
    print("="*50)
    print("TTS Sistemi Kurulum ve İndirme Betiği")
    print("="*50)
    
    branch = get_current_branch()
    print(f"[*] Mevcut Git branch'i tespit edildi: {branch}")
    
    # 1. Kök dizin temel bağımlılıklarını kur
    if os.path.isfile("requirements.txt"):
        run_command(f"{sys.executable} -m pip install -r requirements.txt", "Temel requirements.txt bağımlılıkları yükleniyor")
    else:
        print("[-] requirements.txt bulunamadı, bu adım atlanıyor.")
        
    if branch == "main":
        run_command(f"{sys.executable} -m pip install fastapi uvicorn websockets jinja2 piper-tts", "Main branch için API bağımlılıkları yükleniyor")
    else:
        print(f"[*] '{branch}' ortamı tespit edildi. API ve sunucu gereksinimleri (fastapi, websockets vb.) atlanıyor.")
        
    # 2. VoxCPM model kütüphanesini ve kendi bağımlılıklarını kur
    if os.path.isdir("VoxCPM"):
        run_command(f"{sys.executable} -m pip install -e VoxCPM", "VoxCPM motoru ve bağımlılıkları yükleniyor")
    else:
        print("[-] VoxCPM dizini bulunamadı, bu adım atlanıyor.")
        
    # 3. Trendyol TTS Model dosyalarını kontrol et ve eksikse indir
    check_and_download_trendyol_tts()
    
    # 4. Piper Fallback Model dosyalarını kontrol et ve eksikse indir (Sadece main branch)
    if branch == "main":
        check_and_download_piper_model()
    else:
        print(f"[*] '{branch}' ortamında Piper Fallback motoru kullanılmadığı için indirme atlanıyor.")
    
    print("\n" + "="*50)
    print("[+] Kurulum işlemleri tamamlandı! Servisi başlatmak için aşağıdaki komutu kullanabilirsiniz:")
    print("    python -m service.main")
    print("="*50)

if __name__ == "__main__":
    main()
