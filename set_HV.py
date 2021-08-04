import argparse
from SndCaenManager import SndCaenManager

def main():
    parser = argparse.ArgumentParser('Setting the HV')
    parser.add_argument('mode', type=str, help='Precise the operaton mode (off, idle or operation)')
    parser.add_argument('--daqs', nargs='+', default=None, help='Precise the DAQ boards')
    parser.add_argument('--verbose', '-v', action='store_true')
    args = parser.parse_args()
    
    confPath = 'config_full.toml'   
    manager = SndCaenManager(confPath)

    set_HV(args.mode, args.daqs, manager, verbose=args.verbose)

def set_HV(mode, daqs, manager: SndCaenManager, **kwargs):
    manager.switchHV(mode, daqs)

if __name__ == '__main__':
    main()