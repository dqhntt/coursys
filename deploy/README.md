## Proddev VM Setup

Start with a `vagrant up`. Create `courses/localsettings.py` with `localsettings-proddev-example.py` as a template.
In the VM (`vagrant ssh`),
```sh
cd /coursys
docker-compose -f docker-compose.yml -f docker-compose-proddev.yml up -d
./manage.py migrate
./manage.py loaddata fixtures/*.json
./manage.py update_index
make proddev-start-all
```

## Demo Server Setup

Create a VM.
```sh
sudo apt install chef
git clone https://github.com/sfu-fas/coursys.git
cd coursys/
git checkout some-branch
sudo chef-solo -c ./deploy/solo.rb -j ./deploy/run-list.json # will fail at nginx step because of missing cert...
sudo cp deploy/cookbooks/coursys/files/nginx-bootstrap.conf /etc/nginx/sites-enabled/default
sudo certbot --nginx certonly
sudo chef-solo -c ./deploy/solo.rb -j ./deploy/run-list.json
cd
# rm -rf coursys # probably
cd /coursys
# probably edit /coursys/courses/localsettings.py with localsettings-demo-example.py as a template
# get demo data dumped from production (./manage.py dump_demo_data > /tmp/demodata.json)
make proddev-start-all
./manage.py migrate
./manage.py load_demo_data demodata.json 
```


## Production Server Setup

Get a VM. Do a `ssh-copy-id`.

```sh
sudo apt install git chef
sudo adduser coursys
#sudo gpasswd -a admin coursys
git clone -b deployed-2020 https://github.com/sfu-fas/coursys.git
cd coursys
# check ./deploy/solo.rb and ./deploy/run-list-production.json
sudo chef-solo -c ./deploy/solo.rb -j ./deploy/run-list-production.json
# rm -rf ~/coursys # probably: it's in /coursys now 
sudo certbot --nginx certonly
```

To bootstrap the SSL certificates, either copy appropriate certs from /etc/letsencrypt/live/
or comment-out the SSL server in /etc/nginx/sites-enabled/default and `sudo certbot --nginx certonly`.

Check local settings:
```sh
sudo nano -w /coursys/courses/localsettings.py
sudo nano -w /coursys/courses/secrets.py
```

TODO: disable coursys user password; coursys user sudo only service restarts; SSH cert only