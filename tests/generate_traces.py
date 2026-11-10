# gera os dois traces adicionais de forma determinística

from pathlib import Path

OUT = Path(__file__).parent

# repete 100 vezes uma sequência em que LRU e SecondChance escolhem vítimas diferentes
pages_a = [0, 1, 2, 3, 0, 4] * 100
# converte os números de página em endereços com deslocamentos variados
addresses_a = [page * 256 + (index * 17) % 256 for index, page in enumerate(pages_a)]
# grava os 600 endereços, um por linha
(OUT / "trace_lru_vs_clock.in").write_text(
    "\n".join(map(str, addresses_a)) + "\n", encoding="utf-8"
)

# alterna quatro fases com páginas quentes e varreduras por regiões parcialmente sobrepostas
pages_b = []
for phase in range(4):
    # alterna a base entre as páginas 0 e 16
    base = (phase % 2) * 16
    hot_pattern = [base, base + 1, base, base + 2,
                   base, base + 3, base, base + 1]
    # gera 128 acessos às páginas quentes e 64 acessos de varredura
    pages_b.extend(hot_pattern * 16)
    pages_b.extend(base + 4 + (index % 20) for index in range(64))
# converte as páginas da segunda sequência em endereços virtuais
addresses_b = [page * 1024 + (index * 37) % 1024 for index, page in enumerate(pages_b)]
# grava os 768 endereços, um por linha
(OUT / "trace_fases.in").write_text(
    "\n".join(map(str, addresses_b)) + "\n", encoding="utf-8"
)

# confirma que ambos os traces atendem ao mínimo de 500 acessos
assert len(addresses_a) == 600
assert len(addresses_b) == 768
