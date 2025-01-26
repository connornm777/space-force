#include "asteroid.hpp"

Asteroid::Asteroid(sf::Vector2f pos, sf::Vector2f vel, float rad)
    : GameObject(pos, vel), radius(rad) {
    shape.setRadius(radius);
    shape.setFillColor(sf::Color::Blue);
    shape.setOrigin(radius, radius);

    // Calculate mass proportional to radius squared (constant factor = 0.1)
    mass = 0.1f * radius * radius;
}

void Asteroid::update(float dt) {
    position += velocity * dt;
    shape.setPosition(position);
}

void Asteroid::draw(sf::RenderWindow &window) const {
    window.draw(shape);
}
