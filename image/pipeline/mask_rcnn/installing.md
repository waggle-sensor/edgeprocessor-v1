# Install dependencies and libraries for Mask R-CNN
Especially for tensorflow:

## Install JAVA
Will install Java for bazel. It takes about 50MB.

```
sudo add-apt-repository ppa:webupd8team/java
sudo apt-get update
sudo apt-get install oracle-java8-installer -y
```

## Install Bazel

```
apt-get install unzip
wget --no-check-certificate https://github.com/bazelbuild/bazel/releases/download/0.10.0/bazel-0.10.0-dist.zip
unzip bazel-0.10.0-dist.zip -d bazel-0.10.0-dist
ulimit -c unlimited
mkdir /tmp/bazel_tmp
export TMPDIR=/tmp/bazel_tmp
nano scripts/bootstrap/compile.sh
```
In ```nano scripts/bootstrap/compile.sh``` find line 117:
```
"run "${JAVAC}" -classpath "${classpath}" -sourcepath "${sourcepath}""
```
and add -J-Xms256m -J-Xmx384M as:
```
" run "${JAVAC}" -J-Xms256m -J-Xmx384m -classpath "${classpath}" -sourcepath "${sourcepath}""
```
And then,
```
./complie.sh
```
