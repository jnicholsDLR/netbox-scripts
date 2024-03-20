from extras.scripts import *
from django.utils.text import slugify

from dcim.choices import DeviceStatusChoices, SiteStatusChoices
from dcim.models import Device, DeviceRole, DeviceType, Site, Rack


class NewSiteScript(Script):

    class Meta:
        name = "New Site"
        description = "Provision a new site"

    site_name = StringVar(
        description="Name of the new site"
    )
    pe_switch_count = IntegerVar(
        description="Number of PE (provider edge) switches to create"
    )
    pe_switch_model = ObjectVar(
        description="PE switch model",
        model=DeviceType
    )
    server_count = IntegerVar(
        description="Number of servers to create"
    )
    server_model = ObjectVar(
        description="Server model",
        model=DeviceType
    )

    def run(self, data, commit):

        # Create the new site
        new_site = Site(
            name=data['site_name'],
            slug=slugify(data['site_name']),
            status=SiteStatusChoices.STATUS_PLANNED
        )
        new_site.save()
        self.log_success(f"Created new site: {new_site}")

        # Create a rack per zone
        for zone in ['a', 'b']:
            # foo12_a1, bar34_b1
            rack_name=f"{data['site_name']}_{zone}1"
            new_rack = Rack(
                name=rack_name,
                slug=slugify(rack_name),
                site=new_site,
                status=SiteStatusChoices.STATUS_PLANNED
            )
            new_rack.save()
            self.log_success(f"Created new rack: {new_rack}")

            # Create PE switches per rack
            switch_role = DeviceRole.objects.get(name='pe')
            for i in range(1, data['pe_switch_count'] + 1):
                switch = Device(
                    device_type=data['pe_switch_model'],
                    # pe1a1.foo12, pe2b1.bar34
                    name=f"pe{i}{zone}1.{data['site_name']}",
                    site=new_site,
                    rack=new_rack,
                    status=DeviceStatusChoices.STATUS_PLANNED,
                    device_role=switch_role
                )
                switch.save()
                self.log_success(f"Created new switch: {switch}")

            # Create Servers per rack
            server_role = DeviceRole.objects.get(name='csvr')
            for i in range(1, data['server_count'] + 1):
                server = Device(
                    device_type=data['server_model'],
                    # csvr1a1.foo12, csvr2b1.bar34
                    name=f'csvr{i}{zone}1.{site.slug.lower()}',
                    site=new_site,
                    rack=new_rack,
                    status=DeviceStatusChoices.STATUS_PLANNED,
                    device_role=server_role
                )
                server.save()
                self.log_success(f"Created new server: {server}")

        # Generate a CSV table of new devices
        output = [
            'name,make,model'
        ]
        for device in Device.objects.filter(site=new_site):
            attrs = [
                device.name,
                device.device_type.manufacturer.name,
                device.device_type.model
            ]
            output.append(','.join(attrs))

        return '\n'.join(output)