from mem_sim import MemorySimulator

# cria o simulador com os parâmetros do trace original
mem_simulator = MemorySimulator(page_size=4096, num_tlb_entries=16, num_frames=64, rep_policy='LRU')


# abre o arquivo de entrada com um endereço virtual por linha
arq_test = open("tests/trace.in", "r")

# simula cada acesso e acumula as estatísticas
for addr in arq_test:
    mem_simulator.access_memory(int(addr))
# imprime os contadores ao final do trace
mem_simulator.print_statistics()

