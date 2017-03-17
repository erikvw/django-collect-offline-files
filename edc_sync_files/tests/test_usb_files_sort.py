import unittest


class TestUsbfilesSort(unittest.TestCase):

    def test_sort(self):
        usb_files = [
            '010_201703030256.json', '010_201703030258.json', '010_201703030304.json']
        first_element = usb_files[0]
        second_element = usb_files[1]
        third_element = usb_files[2]
        usb_files.sort()
        self.assertEqual(usb_files[0], first_element)
        self.assertEqual(usb_files[1], second_element)
        self.assertEqual(usb_files[2], third_element)

    def test_sort1(self):
        usb_files = [
            '010_201703030256.json', '010_201703030304.json', '010_201703030258.json']
        first_element = usb_files[0]
        second_element = usb_files[1]
        third_element = usb_files[2]
        usb_files.sort()
        self.assertEqual(usb_files[0], first_element)
        self.assertEqual(usb_files[1], third_element)
        self.assertEqual(usb_files[2], second_element)

if __name__ == '__main__':
    unittest.main()
