#ifndef ASTEROID_HPP
#define ASTEROID_HPP

#include "base_object.hpp"

class Asteroid : public GameObject {
private:
    float radius;
    sf::CircleShape shape;
    float mass; // Mass of the asteroid

public:
    Asteroid(sf::Vector2f pos, sf::Vector2f vel, float rad);
    void update(float dt) override;
    void draw(sf::RenderWindow &window) const override;

    float getRadius() const { return radius; }
    float getMass() const { return mass; } // Getter for mass
};

#endif
