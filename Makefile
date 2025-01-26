# Compiler and flags
CXX = g++
CXXFLAGS = -std=c++17 -Wall -Wextra -I./levels -I./objects

# SFML library paths
SFML_LIBS = -lsfml-graphics -lsfml-window -lsfml-system

# Source files
SOURCES = main.cpp \
          levels/newtonian.cpp \
          objects/rocket.cpp \
          objects/asteroid.cpp \
          objects/bullet.cpp

# Output executable
TARGET = SpaceForce

# Default rule
all: $(TARGET)

# Linking
$(TARGET): $(SOURCES)
	$(CXX) $(CXXFLAGS) $^ -o $@ $(SFML_LIBS)

# Clean rule
clean:
	rm -f $(TARGET)
