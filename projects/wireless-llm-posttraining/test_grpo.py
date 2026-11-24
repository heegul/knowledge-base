import unittest

import torch

from train_grpo import grpo_loss, prepare_group


class GrpoTests(unittest.TestCase):
    def test_group_padding_and_token_mask(self):
        inputs, targets, mask, prefix = prepare_group([1, 2], [[3, 4], [5]], 0, "cpu")
        self.assertEqual(prefix, 2)
        self.assertEqual(inputs["attention_mask"].tolist(), [[1, 1, 1, 1], [1, 1, 1, 0]])
        self.assertEqual(targets.tolist(), [[3, 4], [5, 0]])
        self.assertEqual(mask.tolist(), [[1, 1], [1, 0]])

    def test_original_ratio_and_kl_terms(self):
        current = torch.tensor([[0.0, -0.1], [-0.2, 0.0]], requires_grad=True)
        old = current.detach().clone()
        reference = old.clone()
        mask = torch.ones_like(current)
        advantages = torch.tensor([1.0, -1.0])
        loss, kl = grpo_loss(current, old, reference, mask, advantages, 0.2, 0.04)
        self.assertAlmostEqual(float(loss.detach()), 0.0, places=6)
        self.assertAlmostEqual(kl, 0.0, places=6)
        loss.backward()
        self.assertTrue(torch.isfinite(current.grad).all())
        self.assertLess(float(current.grad[0, 0]), 0)
        self.assertGreater(float(current.grad[1, 0]), 0)

    def test_clipped_positive_advantage(self):
        current = torch.tensor([[0.5]], requires_grad=True)
        old = torch.tensor([[0.0]])
        ref = current.detach().clone()
        loss, _ = grpo_loss(current, old, ref, torch.ones_like(current), torch.tensor([1.0]), 0.2, 0.0)
        self.assertAlmostEqual(float(loss.detach()), -1.2, places=6)


if __name__ == "__main__":
    unittest.main()
