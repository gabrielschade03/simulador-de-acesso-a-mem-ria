from collections import OrderedDict

class MemorySimulator:
    def __init__(self, page_size, num_tlb_entries, num_frames, rep_policy):
        self.page_size = page_size
        self.num_tlb_entries = num_tlb_entries
        self.num_frames = num_frames    
        self.rep_policy = rep_policy

        if rep_policy not in ['LRU', 'SecondChance']:
            raise ValueError("Política de substituição inválida. Use 'LRU' ou 'SecondChance'.")

        # A primeira entrada é a menos recentemente usada.
        self.tlb = OrderedDict()       # página -> frame
        self.page_table = {}           # somente páginas residentes na RAM
        self.frames = [None] * num_frames    # frame(posição) -> página
        self.next_free_frame = 0       # indica o próximo frame livre na RAM

        # Estado das políticas de substituição de páginas, separado da TLB.
        self.page_lru = OrderedDict()  # usado para a política LRU, mantém a ordem de uso das páginas residentes na RAM
        self.reference_bits = [0] * num_frames  # bit de referência da página em cada frame
        self.clock_hand = 0           # próximo frame a verificar no SecondChance

        self.tlb_hits = 0
        self.tlb_misses = 0
        self.page_faults = 0

    def _select_lru_frame(self):
        # Seleciona a página usada há mais tempo e retorna o frame correspondente.
        victim_page = next(iter(self.page_lru))
        return self.page_table[victim_page]

    def _select_second_chance_frame(self):
        # executa o loop do algoritmo Second Chance até encontrar um frame com bit de referência 0.
        while self.reference_bits[self.clock_hand]:
            self.reference_bits[self.clock_hand] = 0
            self.clock_hand = (self.clock_hand + 1) % self.num_frames

        # ao achar a vítima, retorna o frame e move o ponteiro do relógio para o próximo frame.
        victim_frame = self.clock_hand
        self.clock_hand = (self.clock_hand + 1) % self.num_frames
        return victim_frame

    def handle_page_fault(self, page_number):
        # verifica se há algum frame livre na RAM
        if self.next_free_frame < self.num_frames:

            # Se houver, seleciona o próximo frame livre; a página será colocada nele abaixo.
            frame_number = self.next_free_frame
            self.next_free_frame += 1

        # Caso contrário, escolhe o frame da página a substituir conforme a política.
        elif self.rep_policy == "LRU":
            frame_number = self._select_lru_frame()
        else:
            frame_number = self._select_second_chance_frame()

        # Se o frame estiver ocupado, remove os mapeamentos da página vítima.
        victim_page = self.frames[frame_number]
        if victim_page is not None:
            del self.page_table[victim_page]
            del self.page_lru[victim_page]
            self.tlb.pop(victim_page, None)

        # adiciona a nova página no frame escolhido
        self.frames[frame_number] = page_number

        # atualiza a tabela de páginas
        self.page_table[page_number] = frame_number

        # atualiza a lista de uso da página e o bit de referência do frame
        self.page_lru[page_number] = None
        self.reference_bits[frame_number] = 1
        return frame_number

    def update_tlb(self, page_number, frame_number):
        # se a página já estiver na TLB, atualiza o frame e move para o final da fila (mais recentemente usada).
        if page_number in self.tlb:
            self.tlb[page_number] = frame_number
            self.tlb.move_to_end(page_number)
            return

        # se a TLB estiver cheia, remove a entrada menos recentemente usada.
        if len(self.tlb) == self.num_tlb_entries:
            self.tlb.popitem(last=False)
        self.tlb[page_number] = frame_number

    def access_memory(self, virtual_address):
        # Traduz um endereço virtual para sua página correspondente.
        page_number = virtual_address // self.page_size

        # verifica se a tradução está na TLB. caso contrário, verifica a tabela de páginas.
        if page_number in self.tlb:
            self.tlb_hits += 1
            # pega o frame direto da TLB e atualiza a ordem de uso (vai para o final da fila pois acabou de ser usado).
            frame_number = self.tlb[page_number]
            self.tlb.move_to_end(page_number)
        else:
            # se não estiver na TLB, é um TLB miss. verifica a tabela de páginas.
            self.tlb_misses += 1

            # verifica se a página está na tabela de páginas.
            if page_number in self.page_table:

                # se estiver, já pega direto dela
                frame_number = self.page_table[page_number]

            else:
                # se não estiver, é um page fault.
                self.page_faults += 1

                # Aloca um frame para a página; se necessário, substitui uma página residente.
                frame_number = self.handle_page_fault(page_number)

            # atualiza a TLB com a tradução da página que acabou de ser acessada.
            self.update_tlb(page_number, frame_number)

        # atualiza a ordem de uso da página na memória e o bit de referência do frame.
        self.page_lru.move_to_end(page_number) # para a política LRU, move a página para o final da fila (mais recentemente usada)
        self.reference_bits[frame_number] = 1 # para a política SecondChance, marca o frame como referenciado

    def print_statistics(self):
        """Imprime o formato da saída esperada fornecida com o projeto."""
        policy = (
            "LRU (TLB e Memória)" if self.rep_policy == "LRU"
            else "SecondChance (Memória), LRU (TLB)"
        )
        print("=" * 60)
        print("SIMULADOR DE MEMÓRIA - Estatísticas de Acesso")
        print("=" * 60)
        print(f"Política de Substituição:   {policy}")
        print(f"Tamanho da Página:          {self.page_size} bytes")
        print(f"Entradas na TLB:            {self.num_tlb_entries}")
        print(f"Número de Frames:           {self.num_frames}")
        print("-" * 60)
        print(f"TLB Hits:                   {self.tlb_hits:,}")
        print(f"TLB Misses:                 {self.tlb_misses:,}")
        print(f"Page Faults:                {self.page_faults:,}")
        print("=" * 60)
