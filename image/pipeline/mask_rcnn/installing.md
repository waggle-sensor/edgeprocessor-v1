# Install dependencies and libraries for Mask R-CNN
Especially for tensorflow:

## Install JAVA:
Will install Java for bazel. It takes about 50MB.

```
sudo add-apt-repository ppa:webupd8team/java
sudo apt-get update
sudo apt-get install oracle-java8-installer -y
sudo apt-get install oracle-java8-unlimited-jce-policy
```

## Install Bazel:

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

## Install Tensorflow:
```
git clone --recurse-submodules https://github.com/tensorflow/tensorflow.git
cd tensorflow
grep -Rl 'lib64' | xargs sed -i 's/lib64/lib/g'
nano tensorflow/workspace.bzl
```
Replace the following
```
  native.new_http_archive(
      name = "eigen_archive",
      urls = [
          "http://mirror.bazel.build/bitbucket.org/eigen/eigen/get/f3a22f35b044.tar.gz",
          "https://bitbucket.org/eigen/eigen/get/f3a22f35b044.tar.gz",
      ],
      sha256 = "ca7beac153d4059c02c8fc59816c82d54ea47fe58365e8aded4082ded0b820c4",
      strip_prefix = "eigen-eigen-f3a22f35b044",
      build_file = str(Label("//third_party:eigen.BUILD")),
  )
```
with
```
  native.new_http_archive(
      name = "eigen_archive",
      urls = [
          "http://mirror.bazel.build/bitbucket.org/eigen/eigen/get/d781c1de9834.tar.gz",
          "https://bitbucket.org/eigen/eigen/get/d781c1de9834.tar.gz",
      ],
      sha256 = "a34b208da6ec18fa8da963369e166e4a368612c14d956dd2f9d7072904675d9b",
      strip_prefix = "eigen-eigen-d781c1de9834",
      build_file = str(Label("//third_party:eigen.BUILD")),
  )
```




