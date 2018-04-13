# Install dependencies and libraries for Mask R-CNN
Especially for tensorflow:

## Install JAVA
Will install Java for bazel. It takes about 50MB.

```
sudo add-apt-repository ppa:webupd8team/java
sudo apt-get update
sudo apt-get install oracle-java8-installer -y
sudo apt-get install oracle-java8-unlimited-jce-policy
```

## Install Bazel

```
apt-get install unzip zip
wget --no-check-certificate https://github.com/bazelbuild/bazel/releases/download/0.11.1/bazel-0.11.1-dist.zip
unzip bazel-0.11.1-dist.zip -d bazel-0.11.1-dist
ulimit -c unlimited
# mkdir /tmp/bazel_tmp
# export TMPDIR=/tmp/bazel_tmp
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
