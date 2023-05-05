import socket

class MySocket():
    def __init__(self, *args, **kwargs):
        self.custom_arg = kwargs.pop("custom_arg", 18)
        self.test = args.pop(22)

my_socket = MySocket()
print(my_socket.custom_arg) # "default value"

# my_socket2 = MySocket(socket.AF_INET, socket.SOCK_DGRAM, custom_arg="my custom value")
# print(my_socket2.custom_arg) # "my custom value"


class Dog:
    def make_sound(self):
        return 'Woof!'

class Cat:
    def make_sound(self):
        return 'Meow!'

class Pet:
    def __init__(self):
        self.animal = Dog()

    def make_sound(self):
        return self.animal.make_sound()

    def change_animal(self, animal_type):
        if animal_type == 'dog':
            self.animal = Dog()
        else:
            self.animal = Cat()

my_pet = Pet()
print(my_pet.make_sound()) # Output: Woof!

my_pet.change_animal('cat')
print(my_pet.make_sound()) # Output: Meow!


class Animal:
    def make_sound(self):
        pass

class Dog(Animal):
    def make_sound(self, volume):
        return f'Woof! at volume {volume}'

class Cat(Animal):
    def make_sound(self, pitch):
        return f'Meow! at pitch {pitch}'

class Pet:
    def __init__(self, animal_type):
        if animal_type == 'dog':
            self.animal = Dog()
        else:
            self.animal = Cat()

    def make_sound(self, volume=10, pitch=5):
        if isinstance(self.animal, Dog):
            return self.animal.make_sound(volume)
        else:
            return self.animal.make_sound(pitch)

my_pet = Pet('dog')
print(my_pet.make_sound(volume=10)) # Output: Woof! at volume 10

my_pet.animal = Cat()
print(my_pet.make_sound(pitch=5)) # Output: Meow! at pitch 5
