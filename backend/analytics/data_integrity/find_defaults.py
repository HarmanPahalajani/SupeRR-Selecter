import glob
import re

def search():
    patterns = [r'\|\|\s*[\"\']?\d+', r'\|\|\s*8', r'\|\|\s*7', r'\|\|\s*50']
    files = glob.glob('frontend/**/*.tsx', recursive=True) + glob.glob('frontend/**/*.ts', recursive=True)
    files = [f for f in files if 'node_modules' not in f and '.next' not in f]

    for f in sorted(files):
        with open(f, 'r', encoding='utf-8') as src:
            lines = src.readlines()
            for idx, line in enumerate(lines):
                for pat in patterns:
                    if re.search(pat, line):
                        print(f"{f}:{idx+1}: {line.strip()}")
                        break

if __name__ == "__main__":
    search()
