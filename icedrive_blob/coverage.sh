#!/bin/bash

coverage run -m pytest Test || coverage report -m && coverage html
