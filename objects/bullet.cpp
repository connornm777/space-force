#include "bullet.hpp"

Bullet::Bullet(sf::Vector2f pos, sf::Vector2f vel)
    : GameObject(pos, vel), lifetime(30000.0f), timeAlive(0.0f) { // Extended lifetime to 10 seconds
    shape.setRadius(3.0f);
    shape.setFillColor(sf::Color::Yellow);
    shape.setOrigin(3.0f, 3.0f);
}

void Bullet::update(float dt) {
    position += velocity * dt;
    timeAlive += dt;
    shape.setPosition(position);
}

void Bullet::draw(sf::RenderWindow &window) const {
    window.draw(shape);
}

bool Bullet::isExpired() const {
    return timeAlive > lifetime;
}
