import csv
csv_columns = ['No','Name','Country','Vals']
dict_data = [
{'time': 1, 'setpoints': [0,0,0,0], 'measured': [0.1,0.2,-0.1, -0.2], 'input_pressure':30},
{'time': 2, 'setpoints': [0,0,0,0], 'measured': [0.1,0.2,-0.1, -0.2], 'input_pressure':30},
{'time': 3, 'setpoints': [0,0,0,0], 'measured': [0.1,0.2,-0.1, -0.2], 'input_pressure':30},
{'time': 4, 'setpoints': [0,0,0,0], 'measured': [0.1,0.2,-0.1, -0.2], 'input_pressure':30},
{'_command': 'SET', '_args':"0,4,6"},
{'time': 5, 'setpoints': [0,0,0,0], 'measured': [0.1,0.2,-0.1, -0.2], 'input_pressure':30},
]
csv_file = "Names.csv"

# Import a few utility modules
import sys
sys.path.insert(0, 'utils')
from serial_handler import SerialHandler


if __name__ == "__main__":
    ser = SerialHandler()
    ser.read_serial_settings()
    ser.initialize()
    ser.save_init('TESTING.csv')

    for line in dict_data:
        ser.save_data_line(line)

    ser.shutdown()