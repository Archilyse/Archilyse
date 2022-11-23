#!/usr/bin/env bash

: '
If you want to install the system packages without reinstalling the python virtualenv use
RECREATE_VENV=0 make install
'

python_env_name='slam'
docker_short_version='20.10.11'
docker_version='5:20.10.17~3-0~ubuntu-focal'
ifcopenshell_version=python-31-v0.7.0-1b1fd1e
ifcopenshell_target_dir="$(pwd -P)/ifc_reader"
cmake_version='3.16.8'
vtk_version_major='9.2'
vtk_version='9.2.0.rc2'
vtk_version_python='9.2.0rc2'

case $SHELL in
*/zsh)
  rc=~/.zshrc # assume Zsh
  gcloud_inc_file=~/google-cloud-sdk/path.zsh.inc
  ;;
*)
  rc=~/.bashrc # assume Bash
  gcloud_inc_file=~/google-cloud-sdk/path.bash.inc
  ;;
esac

system_dependencies() {
  sudo add-apt-repository ppa:ubuntugis/ppa -y
  sudo apt-get update --fix-missing
  sudo apt-get install -y --allow-downgrades \
      build-essential \
      cmake \
      g++ \
      bzip2 \
      libssl-dev \
      zlib1g-dev \
      libbz2-dev \
      libreadline-dev \
      libsqlite3-dev \
      wget \
      curl \
      llvm \
      libncurses5-dev \
      libncursesw5-dev \
      xz-utils \
      tk-dev \
      tk \
      liblzma-dev \
      python-openssl \
      libnss3 \
      git \
      python-dev \
      gdal-bin \
      libgdal-dev \
      libspatialindex-dev \
      libeigen3-dev \
      libgmp-dev \
      libgmpxx4ldbl \
      libmpfr-dev \
      libboost-dev \
      libboost-thread-dev \
      libtbb-dev \
      libffi-dev \
      libpq-dev \
      python3-pip \
      postgresql-client-common \
      postgresql-client \
      graphviz \
      libmagickwand-dev \
      xvfb \
      unzip \
      fonts-liberation

  rm ~/.cache/matplotlib -rf
  fc-cache -f -v

  # Install GEOS common version for pygeos and shapely. To be deleted once shapely is upgraded to 2.0
  wget http://download.osgeo.org/geos/geos-3.10.3.tar.bz2 && \
  tar xvfj geos-3.10.3.tar.bz2 && \
  mkdir -p geos-3.10.3/build && \
  cd geos-3.10.3/build  && \
  cmake .. -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=/usr && \
  make && \
  sudo make install && \
  cd ../.. && \
  rm -rf geos-3.10.3 && \
  rm geos-3.10.3.tar.bz2
}

vtk (){
  # VTK is only used for some quavis tests
  ## Download and install CMake 3.16.8
  wget https://github.com/Kitware/CMake/releases/download/v${cmake_version}/cmake-${cmake_version}-Linux-x86_64.tar.gz
  tar -zxvf cmake-${cmake_version}-Linux-x86_64.tar.gz
  sudo cp -r cmake-${cmake_version}-Linux-x86_64/* /usr/
  rm cmake-${cmake_version}-Linux-x86_64.tar.gz

  ## Download and build VTK
  sudo apt-get install -y libavcodec-dev \
      libavformat-dev \
      libavutil-dev \
      libboost-dev \
      libdouble-conversion -dev\
      libeigen3-dev \
      libexpat1-dev \
      libfontconfig-dev \
      libfreetype6-dev \
      libglew-dev \
      libhdf5-dev \
      libjpeg-dev \
      libjsoncpp-dev \
      liblz4-dev \
      liblzma-dev \
      libnetcdf-dev \
      libnetcdf-cxx -legacy-dev\
      libogg-dev \
      libpng-dev \
      libpython3-dev \
      libqt5opengl5-dev \
      libqt5x11extras5-dev \
      libsqlite3-dev \
      libswscale-dev \
      libtheora-dev \
      libtiff-dev \
      libxml2-dev \
      libxt-dev \
      qtbase5-dev \
      qttools5-dev \
      zlib1g-dev \
      libx11-xcb1 \
      libx11-xcb-dev \
      libxcursor-dev
  wget "https://www.vtk.org/files/release/${vtk_version_major}/VTK-${vtk_version}.tar.gz"
  tar -zxvf VTK-${vtk_version}.tar.gz
  mkdir VTK-build
  cd VTK-build && ccmake ../VTK-${vtk_version}
  sudo make install -j$(($(nproc) - 1))
  cd .. && rm -rf VTK-build/ VTK-${vtk_version}/ VTK-${vtk_version}.tar.gz
  sudo apt-get clean
}

python() {
  if [[ ! -d "${HOME}/.pyenv" ]]; then
    echo "${HOME}/.pyenv does not exists, installing pyenv"
    curl https://pyenv.run | bash
    grep -qxF "export PATH=${HOME}/.pyenv/bin:\$PATH" ${rc} || echo "export PATH=${HOME}/.pyenv/bin:\$PATH" >> ${rc} && \
    grep -qxF 'eval "$(pyenv init -)"' ${rc} || echo "export PATH=${HOME}/.pyenv/bin:\$PATH" >> ${rc} && \
    grep -qxF 'eval "$(pyenv virtualenv-init -)"' ${rc} || echo 'eval "$(pyenv virtualenv-init -)"' >> ${rc} && \
    echo 'eval "$(pyenv init -)"' >>${rc}
    echo 'eval "$(pyenv virtualenv-init -)"' >>${rc}
    export PATH=${HOME}/.pyenv/bin:$PATH
    pyenv init -
    pyenv virtualenv-init -
  fi

  if [[ -d "${HOME}/.pyenv/versions/${PYTHON_VERSION}" ]]; then
    echo "python ${PYTHON_VERSION} installed"
  else
    echo "python version not installed. Installing new python version"
    cd /home/${USER}/.pyenv/plugins/python-build/../.. && git pull && cd -
    pyenv install ${PYTHON_VERSION}
  fi

  sudo pip3 install pip setuptools wheel virtualenv virtualenvwrapper --upgrade
  grep -q ". /usr/local/bin/virtualenvwrapper.sh" ${rc} || echo ". /usr/local/bin/virtualenvwrapper.sh" >>${rc}
  grep -q "WORKON_HOME=" ${rc} || echo "WORKON_HOME=~/.virtualenvs" >>${rc}
  mkdir -p ~/.virtualenvs

  if [[ -z ${RECREATE_VENV} ]] || [[ ${RECREATE_VENV} == 1 ]]; then
    rm -rf ~/.virtualenvs/${python_env_name} || true
    virtualenv ~/.virtualenvs/${python_env_name} --python="${HOME}"/.pyenv/versions/${PYTHON_VERSION}/bin/python
    ~/.virtualenvs/${python_env_name}/bin/pip install pip wheel --upgrade
    ~/.virtualenvs/${python_env_name}/bin/pip install -r dev_requirements.txt
    ~/.virtualenvs/${python_env_name}/bin/pip install "https://www.vtk.org/files/release/${vtk_version_major}/vtk-${vtk_version_python}-cp310-cp310-manylinux_2_17_x86_64.manylinux2014_x86_64.whl"
  else
    echo "Skipping environment creation/recreation due to flag RECREATE_VENV"
  fi

  # install ifcopenshell
  wget -P ${ifcopenshell_target_dir} https://s3.amazonaws.com/ifcopenshell-builds/ifcopenshell-${ifcopenshell_version}-linux64.zip && \
  unzip -o ${ifcopenshell_target_dir}/ifcopenshell-${ifcopenshell_version}-linux64.zip -d ${ifcopenshell_target_dir} && \
  rm ${ifcopenshell_target_dir}/ifcopenshell-${ifcopenshell_version}-linux64.zip

  ## Create Log folder
  sudo mkdir -p /var/log/slam && sudo chown -R $USER:$USER /var/log/slam
  # Python wand library -> ImageMagick config
  sudo cp docker/configs/image-magick-policy.xml /etc/ImageMagick-6/policy.xml
}

docker () {
  ##Google Cloud libraries
  bash bin/install_gcloud.sh
  grep -qxF "source ${gcloud_inc_file}" ${rc} || echo "source ${gcloud_inc_file}" >> ${rc}
  source ${gcloud_inc_file}
  gcloud config set project "${GCP_REGISTRY_PROJECT}"

  ## Docker installation
  if /usr/bin/docker --version | grep "Docker version ${docker_short_version}" &> /dev/null; then
      echo "correct version of docker installed"
  else
      curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add - &&
      sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
      sudo apt-get update &&
      sudo apt-get install -y apt-transport-https ca-certificates curl software-properties-common &&
      docker_version=${docker_version} bash bin/update_docker.sh &&
      sudo gpasswd -a "${USER}" docker &&
      sudo usermod -a -G docker $USER &&
      sudo service docker restart
  fi
}

frontend() { # Reload after executing this to get the correct node version in terminal
  ## Nodejs & prettier
  curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.1/install.sh | bash && \
  export NVM_DIR="$HOME/.nvm"  && \
  [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
  nvm install $NODE_VERSION
  nvm alias default $NODE_VERSION 
  source ${rc} && \
  npm install -g typescript@4.0.3 && \
  npm install -g npm@8.5.1 && \
  npm install -g prettier@2.2.1 && \
  npm install -g @angular/cli@9.0.4 && \
  npm install -g @percy/cli@v1.6.1

  # from test docker container
  if ! command -v google-chrome &> /dev/null
  then
    echo "google-chrome could not be found"
    wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb && \
    sudo dpkg -i google-chrome-stable_current_amd64.deb && \
    rm google-chrome-stable_current_amd64.deb
  fi
  CHROME_MAJOR_VERSION=$(google-chrome --version | sed -E "s/.* ([0-9]+)(\.[0-9]+){3}.*/\1/") && \
  CHROME_DRIVER_VERSION=$(wget --no-verbose -O - \
      https://chromedriver.storage.googleapis.com/LATEST_RELEASE_${CHROME_MAJOR_VERSION}) && \
  wget --no-verbose -O /tmp/chromedriver_linux64.zip \
      https://chromedriver.storage.googleapis.com/$CHROME_DRIVER_VERSION/chromedriver_linux64.zip && \
  sudo rm -rf /opt/selenium/chromedriver && \
  sudo unzip /tmp/chromedriver_linux64.zip -d /opt/selenium && \
  sudo mv /opt/selenium/chromedriver /usr/bin/chromedriver && \
  sudo rm -r /tmp/chromedriver_linux64.zip /opt/selenium
}

aliases() {
  alias rebase="git stash && git checkout develop && git pull && git fetch -p && git checkout - && git rebase develop && git stash pop"
  alias git-graph="git log --graph --pretty='%Cred%h%Creset -%C(auto)%d%Creset %s %Cgreen(%ad) %C(bold blue)<%an>%Creset' --date=short"
  alias update="git fetch -p && git pull"
  alias refresh="!git fetch --all -p && git rebase origin/develop"
}

case "$1" in
  --all)
    system_dependencies
    python
    docker
    frontend
    ;;
  --frontend)
    frontend
    ;;
  --python)
    python
    ;;
  --vtk)
    vtk
    ;;
  --system_dependencies)
    system_dependencies
    ;;
  --docker)
    docker
    ;;
esac