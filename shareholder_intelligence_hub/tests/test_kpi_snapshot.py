# -*- coding: utf-8 -*-

from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestKpiSnapshotSigns(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company

        cls.income_account = cls.env['account.account'].search(
            [('account_type', '=', 'income'), ('company_ids', 'in', cls.company.ids)],
            limit=1,
        )
        cls.equity_account = cls.env['account.account'].search(
            [('account_type', '=', 'equity'), ('company_ids', 'in', cls.company.ids)],
            limit=1,
        )
        cls.payable_account = cls.env['account.account'].search(
            [('account_type', '=', 'liability_payable'), ('company_ids', 'in', cls.company.ids)],
            limit=1,
        )
        cls.cash_account = cls.env['account.account'].search(
            [('account_type', '=', 'asset_cash'), ('company_ids', 'in', cls.company.ids)],
            limit=1,
        )

    def _post_move(self, credit_account, debit_account, amount, date):

        move = self.env['account.move'].create({
            'move_type': 'entry',
            'company_id': self.company.id,
            'date': date,
            'line_ids': [
                (0, 0, {
                    'account_id': debit_account.id,
                    'debit': amount,
                    'credit': 0.0,
                }),
                (0, 0, {
                    'account_id': credit_account.id,
                    'debit': 0.0,
                    'credit': amount,
                }),
            ],
        })
        move.action_post()
        return move



    def test_revenue_is_positive(self):

        if not (self.income_account and self.cash_account):
            self.skipTest(
                "There are no income/asset_cash accounts in the test chart of accounts"
            )

        snapshot_date = '2026-08-01'

        snapshot_before = self.env['dashboard.kpi.snapshot'].create({
            'company_id': self.company.id,
            'snapshot_date': snapshot_date,
        })

        revenue_before = snapshot_before.revenue_ytd
        snapshot_before.unlink()

        self._post_move(
            credit_account=self.income_account,
            debit_account=self.cash_account,
            amount=1000.0,
            date=snapshot_date,
        )

        snapshot_after = self.env['dashboard.kpi.snapshot'].create({
            'company_id': self.company.id,
            'snapshot_date': snapshot_date,
        })

        self.assertGreater(
            snapshot_after.revenue_ytd,
            0,
            "revenue_ytd must be positive after a normal sale"
        )

        self.assertAlmostEqual(
            snapshot_after.revenue_ytd - revenue_before,
            1000.0,
            places=2,
            msg="revenue_ytd must increase by exactly the posted amount"
        )



    def test_payable_is_positive(self):

        if not (self.payable_account and self.cash_account):
            self.skipTest("There are no liability_payable/asset_cash accounts in the test chart of accounts")

        self._post_move(
            credit_account=self.payable_account,
            debit_account=self.cash_account,
            amount=500.0,
            date='2026-08-02',
        )

        snapshot = self.env['dashboard.kpi.snapshot'].create({
            'company_id': self.company.id,
            'snapshot_date': '2026-08-02',
        })

        self.assertGreater(
            snapshot.ap_total, 0,
            "ap_total must be positive (represents the amount owed)"
        )



    def test_equity_is_positive_in_normal_case(self):
        if not (self.equity_account and self.cash_account):
            self.skipTest(
                "There are no equity/asset_cash accounts in the test chart of accounts"
            )

        self._post_move(
            credit_account=self.equity_account,
            debit_account=self.cash_account,
            amount=2000.0,
            date='2026-08-03',
        )

        snapshot = self.env['dashboard.kpi.snapshot'].create({
            'company_id': self.company.id,
            'snapshot_date': '2026-08-03',
        })

        self.assertGreater(
            snapshot.total_equity,
            0,
            "total_equity must be positive in the normal case (capital contribution)"
        )