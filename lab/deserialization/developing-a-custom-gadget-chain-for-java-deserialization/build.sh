#!/bin/zsh

rm -rf ./obj/
javac -d obj ./src/**/*.java && \
  jar --create --verbose --file=gen.jar --main-class=Main -C obj/ . && \
  chmod +x gen.jar
