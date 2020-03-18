Vagrant.configure("2") do |config|
    # Based on the official Hashicorp Ubuntu box image
    config.vm.box = "hashicorp/bionic64"
    # Provision with ansible
    config.vm.provision "ansible" do |ansible|
      ansible.playbook = "provisioning/playbook.yml"
      # Tell Ansible to use python version 3
      ansible.extra_vars = { ansible_python_interpreter:"/usr/bin/python3" }
    end
    # Sets ports forwarding rules
    config.vm.network "forwarded_port", guest: 5000, host: 5000
    config.vm.network "forwarded_port", guest: 9000, host: 9000
  end