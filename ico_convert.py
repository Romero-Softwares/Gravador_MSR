from PIL import Image, ImageOps, ImageDraw
import os


def criar_icone_circular(input_path, output_path):
    # 1. Abrir a imagem original
    img = Image.open(input_path).convert("RGBA")

    # 2. Criar uma máscara circular
    size = img.size
    mask = Image.new('L', size, 0)
    draw = ImageDraw.Draw(mask)
    # Desenha o círculo branco (preenche a máscara)
    draw.ellipse((0, 0) + size, fill=255)

    # 3. Aplicar a máscara à imagem (recorta o redondo)
    output = Image.new('RGBA', size, (0, 0, 0, 0))
    output.paste(img, (0, 0), mask=mask)

    # 4. Salvar como .ico com múltiplos tamanhos (padrão Windows)
    # O Windows usa de 16x16 até 256x256
    icon_sizes = [(16, 16),(32, 32),(48, 48),(64, 64), (128, 128), (256, 256)]
    output.save(output_path, format='ICO', sizes=icon_sizes)
    print(f"Sucesso! Ícone circular salvo em: {output_path}")

criar_icone_circular("icone.png", "icone.ico") # input_path to output_path image
