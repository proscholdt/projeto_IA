import subprocess

def rodar_script(caminho):
    print(f"\n--- Executando {caminho} ---")
    resultado = subprocess.run(["python", caminho], capture_output=True, text=True)
    print(resultado.stdout)
    if resultado.stderr:
        print("Erros:", resultado.stderr)

if __name__ == "__main__":
    scripts = [
        "transformadores/1_base_vetorial.py",
        "transformadores/2_limparDados_GerarChunks.py",
        "transformadores/3_limparChunks.py"
    ]

    for script in scripts:
        rodar_script(script)

    print("\n✅ Processamento finalizado!")
