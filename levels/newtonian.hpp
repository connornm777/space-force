#ifndef NEWTONIAN_HPP
#define NEWTONIAN_HPP

#include "base_level.hpp"

class NewtonianLevel : public BaseLevel {
private:
    float blackHoleRadius = 100.0f;

public:
    void draw(sf::RenderWindow &window) override;
};

#endif
