import os
from time import sleep

from django.conf import settings
from django.test.testcases import TestCase
from django.test.utils import tag

from faker import Faker

from edc_example.models import TestModel

from ..classes import TransactionDumps


@tag('TestTransactionOrder')
class TestBatchSeq(TestCase):

    def setUp(self):
        TestCase.setUp(self)
        self.faker = Faker()

    def test_file_identifier_first_time(self):
        #  Create transactions
        TestModel.objects.using('client').create(f1=self.faker.name())
        TestModel.objects.using('client').create(f1=self.faker.name())

        # Dump transaction
        path = os.path.join(settings.MEDIA_ROOT, "transactions", "outgoing")
        tx_dumps = TransactionDumps(path, using='client', hostname="010")
        self.assertTrue(tx_dumps.is_exported_to_json)

        self.assertTrue(tx_dumps.batch_id)
        self.assertTrue(tx_dumps.batch_seq)
        self.assertEqual(tx_dumps.batch_seq, tx_dumps.batch_id) # first time should be equal
        
    def test_file_identifier_second_time(self):
        #  Create transactions
        TestModel.objects.using('client').create(f1=self.faker.name())
        TestModel.objects.using('client').create(f1=self.faker.name())

        # Dump transaction 1
        path = os.path.join(settings.MEDIA_ROOT, "transactions", "outgoing")
        tx_dumps_1 = TransactionDumps(path, using='client', hostname="010")
        self.assertTrue(tx_dumps_1.is_exported_to_json)
        sleep(1)
        batch_id_1 = tx_dumps_1.batch_id
        
        TestModel.objects.using('client').create(f1=self.faker.name())
        TestModel.objects.using('client').create(f1=self.faker.name())
        sleep(1)
        # Dump transaction 2
        path = os.path.join(settings.MEDIA_ROOT, "transactions", "outgoing")
        tx_dumps_2 = TransactionDumps(path, using='client', hostname="010")
        self.assertTrue(tx_dumps_2.is_exported_to_json)

        batch_id_2 = tx_dumps_2.batch_id
        batch_seq_2 = tx_dumps_2.batch_seq
        
        self.assertEqual(str(batch_id_1), batch_seq_2) # should be equal to previous batch_seq
        self.assertNotEqual(batch_id_1, batch_id_2) # should not be equal, assigned a new tx_pk
        


    @tag('test_file_identifier_with_synced_tx')
    def test_file_identifier_second_time1(self):
        
        #  Create transactions
        TestModel.objects.using('client').create(f1=self.faker.name())
        TestModel.objects.using('client').create(f1=self.faker.name())

        # Dump transaction 1
        path = os.path.join(settings.MEDIA_ROOT, "transactions", "outgoing")
        tx_dumps_1 = TransactionDumps(path, using='client', hostname="010")
        self.assertTrue(tx_dumps_1.is_exported_to_json)
        batch_id_1 = tx_dumps_1.batch_id
        batch_seq_1 = tx_dumps_1.batch_seq
        
        TestModel.objects.using('client').create(f1=self.faker.name())
        TestModel.objects.using('client').create(f1=self.faker.name())
        sleep(1)
        # Dump transaction 2
        path = os.path.join(settings.MEDIA_ROOT, "transactions", "outgoing")
        tx_dumps_2 = TransactionDumps(path, using='client', hostname="010")
        self.assertTrue(tx_dumps_2.is_exported_to_json)
        
        sleep(1)
        batch_id_2 = tx_dumps_2.batch_id
        batch_seq_2 = tx_dumps_2.batch_seq
        batch_seq_1 = str(batch_seq_1)

        self.assertEqual(batch_seq_2, str(batch_id_1)) # should be equal to previous batch_seq
        self.assertNotEqual(batch_id_1, batch_id_2) # should not be equal, assigned a new tx_pk
        
        #  Create transactions
        TestModel.objects.using('client').create(f1=self.faker.name())
        TestModel.objects.using('client').create(f1=self.faker.name())
        sleep(1)
        # Dump transaction 3
        path = os.path.join(settings.MEDIA_ROOT, "transactions", "outgoing")
        tx_dumps_3 = TransactionDumps(path, using='client', hostname="010")
        self.assertTrue(tx_dumps_3.is_exported_to_json)
         
        batch_id_3 = tx_dumps_3.batch_id
        batch_seq_3 = tx_dumps_3.batch_seq
         
        self.assertEqual(str(batch_id_2), batch_seq_3) # should be equal to previous batch_seq
        self.assertNotEqual(batch_id_3, batch_id_2) # should not be equal, assigned a new tx_pk
