import argparse
from SndCaenManager import SndCaenManager

def main():
    parser = argparse.ArgumentParser('Setting the LV')
    parser.add_argument('mode', type=str, help='Precise the operaton mode (on or off)')
    parser.add_argument('--daqs', nargs='+', default=None, help='Precise the DAQ boards')
    parser.add_argument('--verbose', '-v', action='store_true')
    args = parser.parse_args()
    
    confPath = 'config_SND.toml'   
    manager = SndCaenManager(confPath)

    set_HV(args.mode, args.daqs, manager, verbose=args.verbose)

def set_HV(mode, daqs, manager: SndCaenManager, **kwargs):
    if mode == 'on':
        manager.switchLV(True, daqs)
    elif mode == 'off':
        manager.switchLV(False, daqs)
    else:
        print('Incorrect operation mode (specify either on or off')

if __name__ == '__main__':
    main()