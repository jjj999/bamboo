
import unittest

from bamboo.util.string import CircularChar, SerialString


class TestUtilString(unittest.TestCase):
        
    def test_char(self):
        char = CircularChar()
        for _ in range(char.END):
            char.next()
            
        self.assertEqual(char.current, CircularChar.TAIL)
        
    def test_serial_string_up(self):
        serial = SerialString(2)
        
        for _ in range(CircularChar.END + 1):
            for _ in range(CircularChar.END + 1):
                serial.next()
            self.assertEqual(serial.current[-1], CircularChar.TAIL)
        
        full = serial.next()
        self.assertTrue(full is None)

    def test_serial_string_nonup(self):
        serial = SerialString(2)
        
        self.assertEqual(serial.next(up=False), "00")
        self.assertEqual(serial.current, "00")
        
                
if __name__ == "__main__":
    unittest.main()
