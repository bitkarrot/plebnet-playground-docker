# Generates docker-compose from command line.
#
# For each service identified at command line, this we identify other dependent services and add them to the config.

# +
from omegaconf import OmegaConf
import sys


architectures = {
        "Intel x64": 'x86_64-linux-gnu',
        'OSX 64-bit': 'aarch64-linux-gnu',
        'arm 32-bit': 'arm-linux-gnueabihf',
        'ARM64 linux': 'aarch64-linux-gnu',
}

# +
cli_args = OmegaConf.from_cli()

try:
    arch = cli_args['ARCH']
except KeyError:
    print('Need to supply ARCH. Supported architectures:')
    for k, v in architectures.items():
        print('\t{}: ARCH={}'.format(k, v))
    sys.exit()

conf = OmegaConf.load('docker-compose.yaml.template')

# merge in architecture
conf = OmegaConf.merge(OmegaConf.create(dict(ARCH=arch)), conf)


try:
    services = cli_args['services'].split(',')
except KeyError:
    print('Using default services')
    services = [service for service in conf.services]

print('requested services:\t{}'.format(', '.join(sorted(services))))

required_services = set()

for service_name in services:
    if service_name in conf.services:
        required_services.add(service_name)
        depends = conf.services[service_name].get('depends_on', [])
        for service in depends:
            required_services.add(service)
        links = conf.services[service_name].get('links', [])
        for service in links:
            required_services.add(service)
    else:
        print('{} service not yet available in plebnet-playground!'.format(
            service_name))
        print('available services:')
        for service in conf.services:
            print('\t{}'.format(service))
        print('Add the configuration for {} to docker-compose.yaml.template and run again.'.format(
            service_name))
        sys.exit()

print('required services:\t{}'.format(', '.join(sorted(required_services))))

for service_name in list(conf.services):
    if service_name not in required_services:
        conf.services.pop(service_name)

# dashboard keyword
conf['USE_TEST_DATA'] = cli_args.get('ARCH', False)

try:
    OmegaConf.resolve(conf)
except:
    print(OmegaConf.to_yaml(conf))
    raise

conf.pop('ARCH')
conf.pop('USE_TEST_DATA')

with open('docker-compose.yaml', 'w') as f:
    f.write(OmegaConf.to_yaml(conf))

print('wrote required services to docker-compose.yaml')
