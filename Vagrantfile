# -*- mode: ruby -*-
# vi: set ft=ruby :

$setup1 = <<SCRIPT1
# misc tools
apt-get install -y vim byobu
# Galley related packages
apt-get install -y python-pip python-dev git libssl-dev

# update pip
pip install -U pip
SCRIPT1

$setup2 = <<SCRIPT2
pip install virtualenvwrapper
su -c '. /usr/local/bin/virtualenvwrapper.sh && mkvirtualenv Galley' -l vagrant

# install Galley
pip install -r /vagrant/requirements.txt
pip install -r /vagrant/test-requirements.txt
pip install -e /vagrant/.

usermod -G docker -a vagrant

echo ". /usr/local/bin/virtualenvwrapper.sh && workon Galley" >> /home/vagrant/.bashrc
SCRIPT2

# Vagrantfile API/syntax version. Don't touch unless you know what you're doing!
VAGRANTFILE_API_VERSION = "2"

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
  config.vm.box = "base"

  config.vm.box = "raring"
  config.vm.box_url = "http://cloud-images.ubuntu.com/vagrant/raring/current/raring-server-cloudimg-amd64-vagrant-disk1.box"

  config.omnibus.chef_version = :latest
  config.berkshelf.enabled = true

  config.vm.provision :chef_solo do |chef|
    chef.add_recipe "apt"
    chef.add_recipe "docker"
  end

  config.vm.provision "shell", inline: $setup1
  config.vm.provision "shell", inline: $setup2
end
