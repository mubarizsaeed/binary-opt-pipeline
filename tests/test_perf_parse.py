import unittest
from pathlib import Path

from pipeline import hotspots, perf_parse, report

FIX = Path(__file__).parent / "fixtures"


class ParseReport(unittest.TestCase):
    def test_symbols_and_header(self):
        rep = perf_parse.parse_report((FIX / "perf_report_sample.txt").read_text())
        self.assertEqual(rep.event, "cycles")
        self.assertEqual(rep.samples, 41000)
        self.assertEqual(len(rep.symbols), 4)
        top = rep.symbols[0]
        self.assertEqual(top.symbol, "sum_above")
        self.assertAlmostEqual(top.percent, 91.84)
        self.assertEqual(top.dso, "branch_mispredict")
        self.assertTrue(top.is_user)
        self.assertFalse(rep.symbols[2].is_user)  # kernel symbol


class ParseStat(unittest.TestCase):
    def test_counts_skip_unsupported(self):
        counts = perf_parse.parse_stat_csv((FIX / "perf_stat_sample.csv").read_text())
        self.assertEqual(counts["cycles"], 52418234911)
        self.assertEqual(counts["branch-misses"], 2101233841)
        self.assertNotIn("L1-dcache-load-misses", counts)


class ParseAnnotate(unittest.TestCase):
    def test_hot_instruction(self):
        ann = perf_parse.parse_annotate((FIX / "perf_annotate_sample.txt").read_text())
        self.assertEqual(len(ann), 8)
        hottest = max(ann, key=lambda a: a.percent)
        self.assertEqual(hottest.address, 0x401155)
        self.assertIn("cmp", hottest.insn)


class Classify(unittest.TestCase):
    def test_branch_prior(self):
        counts = perf_parse.parse_stat_csv((FIX / "perf_stat_sample.csv").read_text())
        self.assertEqual(hotspots.classify(counts), "branch")

    def test_memory_prior(self):
        counts = {"cycles": 1e9, "instructions": 2e8, "branches": 1e7, "branch-misses": 1e4,
                  "LLC-load-misses": 5e6}
        self.assertEqual(hotspots.classify(counts), "memory-latency")

    def test_dep_chain_prior(self):
        counts = {"cycles": 1e9, "instructions": 5e8, "branches": 1e8, "branch-misses": 1e3,
                  "LLC-load-misses": 10, "L1-dcache-load-misses": 100}
        self.assertEqual(hotspots.classify(counts), "dependency-chain")

    def test_rank_attaches_addresses(self):
        rep = perf_parse.parse_report((FIX / "perf_report_sample.txt").read_text())
        counts = perf_parse.parse_stat_csv((FIX / "perf_stat_sample.csv").read_text())
        ann = perf_parse.parse_annotate((FIX / "perf_annotate_sample.txt").read_text())
        spots = hotspots.rank(rep, counts, ann, top_n=3)
        self.assertEqual([s.symbol for s in spots], ["sum_above", "main", "__memset_avx2_unaligned_erms"])
        self.assertEqual(spots[0].prior, "branch")
        self.assertEqual(spots[0].hot_addresses[0], 0x401155)


class Report(unittest.TestCase):
    def test_empty_and_rows(self):
        self.assertIn("No measured results", report.to_markdown([]))
        md = report.to_markdown([{"benchmark": "branch_mispredict", "bottleneck": "branch",
                                  "phase": "A", "speedup": 2.5, "correct": True, "iterations": 1}])
        self.assertIn("2.50x", md)
        self.assertIn("| yes |", md)


if __name__ == "__main__":
    unittest.main()
