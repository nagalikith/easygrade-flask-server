import random

#used to generate hex code

#default length of hex code
config = {"length": 10}

hex_chars = "0123456789abcdef"

def gen_hex(length=None):
  if (type(length) != int or length <= 0):
    length = config["length"]

  res  = ''

  for i in range(length):
    res += hex_chars[random.randint(0, 15)]

  return(res)
