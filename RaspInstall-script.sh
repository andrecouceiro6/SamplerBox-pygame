#!/bin/sh

#1) Como copiar sons para os cartões SD
#docker run -t -i --device=/dev/rdisk2s2 ubuntu:xenial bash
#Ubuntu: sudo mount /dev/disk2 /path

# #2) Como duplicar as imagens de cartão
# #https://raspberrypi.stackexchange.com/questions/311/how-do-i-backup-my-raspberry-pi/312#312

# Build Image: sudo dd if=/dev/rdisk2 bs=1m | gzip > ~/Desktop/Raspberry-PP-Sampler-0.0.img.gz#
# Flash Image: gzip -dc ~/Desktop/Raspberry-PP-Sampler-0.0.img.gz | dd of=/dev/rdisk2 bs=1m status=progress

# 3) Refazer instalação com o mínimo possivel

# 	1) Flash latest Raspbian
# 	2) Copy ssh into root folder
# 	3) Connect Raspberry to Router via eth cable
# 	4) ssh pi@raspberrypi.local
# 	 - If Host key error: ssh-keygen -R raspberrypi.local

# 	5) Install:
 	sudo apt-get update
 	sudo apt-get -y install python-serial
 	sudo apt-get -y install python-numpy
 	sudo apt-get -y install python-pygame

# 	6) Copy project:
	cd ~
	git clone https://github.com/andrecouceiro6/SamplerBox-pygame.git 
	cd SamplerBox-pygame
# 	7) Copy service:
 	sudo cp samplerbox-pygame.service /etc/systemd/system/samplerbox-pygame.service

# 	9) Enable Service
 	sudo systemctl enable samplerbox-pygame

# 	10) Activate SSH via Serial
# 	sudo raspi-config (Interfacing Options-> Serial-> Yes )

# 	11) Set Default Audio Device
# 	sudo raspi-config (Advanced -> Audio -> Force 3.5mm )

# 	12) Set Volume
# 	alsamixer && mount -o remount,rw / && alsactl store
