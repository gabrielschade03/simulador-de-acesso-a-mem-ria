# Testes do simulador

Cada linha de `trace_*.in` contém um endereço virtual decimal. `saida_*.out` traz a saída completa esperada para cada política. Os arquivos `trace.in` e `saidaesperada.in` são os originais fornecidos com o projeto.

| Trace | Acessos | page_size | TLB | Frames | Característica |
| --- | ---: | ---: | ---: | ---: | --- |
| `trace_lru_vs_clock.in` | 600 | 256 | 2 | 4 | Repete as páginas `0,1,2,3,0,4`. A referência recente à página 0 faz LRU e SecondChance escolherem vítimas diferentes. A TLB pequena também produz misses sem page fault. |
| `trace_fases.in` | 768 | 1024 | 16 | 32 | Alterna duas regiões parcialmente sobrepostas; em cada fase há 128 acessos a páginas quentes e 64 acessos de varredura. Mostra localidade, pressão na TLB e substituição após mudança de fase. |

Os deslocamentos são não nulos em parte dos acessos, para verificar que a página é calculada por divisão inteira pelo tamanho da página. `generate_traces.py` recria os dois arquivos de entrada sem aleatoriedade.

Executar todos os testes, incluindo o trace original de 8.043.008 acessos:

```sh
python3 -m unittest discover -s tests -v
```

A suíte executa cada trace adicional nas duas políticas com os parâmetros da tabela. Para executar o exemplo original separadamente, use `python3 main.py` na raiz do projeto.

A suíte também confirma que uma política de substituição inválida é rejeitada com `ValueError` e que a TLB continua usando LRU mesmo quando os frames usam SecondChance.
