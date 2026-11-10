# testa o comportamento do simulador e compara as saídas com os resultados esperados

from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
import sys
import unittest

# localiza a raiz do projeto e a pasta dos arquivos de teste
ROOT = Path(__file__).resolve().parents[1]
TESTS = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

# importa a classe depois de incluir a raiz do projeto no caminho de busca
from mem_sim import MemorySimulator


class MemorySimulatorTests(unittest.TestCase):
    def test_policies_choose_different_victims(self):
        # usa a mesma sequência nas duas políticas para comparar as páginas vítimas
        addresses = [0, 256, 512, 768, 0, 1024]
        expected = {"LRU": 1, "SecondChance": 0}
        for policy, victim in expected.items():
            with self.subTest(policy=policy):
                simulator = MemorySimulator(256, 2, 4, policy)
                for address in addresses:
                    simulator.access_memory(address)
                # a vítima deve sair da RAM e não pode manter uma tradução na TLB
                self.assertNotIn(victim, simulator.page_table)
                self.assertNotIn(victim, simulator.tlb)
                self.assertEqual(simulator.page_faults, 5)

    def test_tlb_miss_can_occur_without_page_fault(self):
        # a página 0 sai da TLB, mas continua residente em um frame
        simulator = MemorySimulator(4, 2, 4, "LRU")
        for address in (0, 4, 8, 0):
            simulator.access_memory(address)
        self.assertEqual((simulator.tlb_hits, simulator.tlb_misses,
                          simulator.page_faults), (0, 4, 3))
        self.assertIn(0, simulator.page_table)

    def test_eviction_invalidates_tlb(self):
        # ao acessar a terceira página com apenas dois frames, a página 0 é substituída
        simulator = MemorySimulator(4, 2, 2, "LRU")
        for address in (0, 4, 8):
            simulator.access_memory(address)
        self.assertNotIn(0, simulator.page_table)
        self.assertNotIn(0, simulator.tlb)
        self.assertEqual(simulator.tlb[2], simulator.page_table[2])

    def test_tlb_uses_lru_even_with_second_chance_for_frames(self):
        # mesmo com SecondChance nos frames, a TLB continua substituindo por LRU
        simulator = MemorySimulator(4, 2, 4, "SecondChance")
        for address in (0, 4, 0, 8):
            simulator.access_memory(address)
        self.assertEqual(list(simulator.tlb), [0, 2])
        self.assertIn(1, simulator.page_table)
        self.assertEqual((simulator.tlb_hits, simulator.tlb_misses,
                          simulator.page_faults), (1, 3, 3))
        # a página 1 gera TLB miss, mas não page fault, pois continua residente
        simulator.access_memory(4)
        self.assertEqual((simulator.tlb_hits, simulator.tlb_misses,
                          simulator.page_faults), (1, 4, 3))

    def test_invalid_policy_is_rejected(self):
        # políticas diferentes de LRU e SecondChance devem ser recusadas
        with self.assertRaises(ValueError):
            MemorySimulator(4096, 16, 64, "FIFO")

    def _compare_trace(self, trace_path, expected_path, parameters):
        # executa todos os endereços de entrada e conta os acessos efetuados
        simulator = MemorySimulator(*parameters)
        accesses = 0
        with trace_path.open(encoding="utf-8") as trace:
            for line in trace:
                if line.strip():
                    accesses += 1
                    simulator.access_memory(int(line))
        # captura a saída impressa para compará-la com o arquivo esperado
        output = StringIO()
        with redirect_stdout(output):
            simulator.print_statistics()
        self.assertEqual(output.getvalue().strip(),
                         expected_path.read_text(encoding="utf-8").strip())
        # cada acesso deve produzir exatamente um hit ou um miss na TLB
        self.assertEqual(simulator.tlb_hits + simulator.tlb_misses, accesses)
        # toda tradução ainda presente na TLB deve corresponder à tabela de páginas
        self.assertTrue(all(simulator.page_table.get(page) == frame
                            for page, frame in simulator.tlb.items()))

    def test_additional_traces(self):
        # executa os dois traces adicionais com LRU e SecondChance
        cases = (
            ("lru_vs_clock", 256, 2, 4),
            ("fases", 1024, 16, 32),
        )
        for name, page_size, tlb_entries, frames in cases:
            for policy in ("LRU", "SecondChance"):
                with self.subTest(trace=name, policy=policy):
                    self._compare_trace(
                        TESTS / f"trace_{name}.in",
                        TESTS / f"saida_{name}_{policy}.out",
                        (page_size, tlb_entries, frames, policy),
                    )

    def test_supplied_trace(self):
        # compara o trace fornecido com a saída oficial do projeto
        self._compare_trace(
            TESTS / "trace.in", TESTS / "saidaesperada.in",
            (4096, 16, 64, "LRU"),
        )


if __name__ == "__main__":
    unittest.main()
