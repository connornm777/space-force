#ifndef BASE_LEVEL_HPP
#define BASE_LEVEL_HPP

#include <SFML/Graphics.hpp>

class BaseLevel {
public:
    virtual ~BaseLevel() = default;

    virtual void draw(sf::RenderWindow &window) = 0;
};

#endif
