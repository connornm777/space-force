#include "rocket.hpp"

Rocket::Rocket(sf::Vector2f pos)
    : GameObject(pos, {0, 0}), angle(0.0f), angularVelocity(0.0f), thrusting(false) {
    shape.setPointCount(3);
    shape.setPoint(0, sf::Vector2f(0.0f, -15.0f));  // Nose
    shape.setPoint(1, sf::Vector2f(-10.0f, 10.0f)); // Left corner
    shape.setPoint(2, sf::Vector2f(10.0f, 10.0f));  // Right corner
    shape.setFillColor(sf::Color::Red);
    shape.setOrigin(0.0f, 0.0f);
}

void Rocket::update(float dt) {
    angle += angularVelocity * dt;
    position += velocity * dt;

    if (position.x < 0) position.x += 1800;
    if (position.x > 1800) position.x -= 1800;
    if (position.y < 0) position.y += 1000;
    if (position.y > 1000) position.y -= 1000;

    shape.setRotation(angle);
    shape.setPosition(position);
    thrusting = false; // Reset thrusting flag each frame
}

void Rocket::draw(sf::RenderWindow &window) const {
    window.draw(shape);

    if (thrusting) {
        sf::ConvexShape flame;
        flame.setPointCount(3);
        flame.setPoint(0, sf::Vector2f(0.0f, 15.0f)); // Flame tip
        flame.setPoint(1, sf::Vector2f(-10.0f, 25.0f)); // Left base
        flame.setPoint(2, sf::Vector2f(10.0f, 25.0f));  // Right base
        flame.setFillColor(sf::Color::Yellow);
        flame.setOrigin(0.0f, 0.0f);
        flame.setRotation(angle);
        flame.setPosition(position);
        window.draw(flame);
    }
}

void Rocket::applyThrust(float dt, bool forward) {
    float rad = angle * M_PI / 180.0f;
    sf::Vector2f thrustDirection = forward
                                       ? sf::Vector2f(std::cos(rad-M_PI/2), std::sin(rad-M_PI/2))
                                       : sf::Vector2f(-std::cos(rad-M_PI/2), -std::sin(rad-M_PI/2));
    velocity += thrustDirection * thrustPower * dt;
    thrusting = forward; // Enable flame animation only for forward thrust
}

void Rocket::applyRotationThrust(float dt, bool clockwise) {
    angularVelocity += (clockwise ? rotationThrust : -rotationThrust) * dt;
}

void Rocket::reset() {
    position = {900.0f, 500.0f};
    velocity = {0.0f, 0.0f};
    angularVelocity = 0.0f;
    angle = 0.0f;
}

Bullet Rocket::shoot() const {
    float rad = angle * M_PI / 180.0f;
    sf::Vector2f bulletVelocity = velocity+sf::Vector2f(std::cos(rad-M_PI/2), std::sin(rad-M_PI/2)) * 100.0f;
    sf::Vector2f bulletPosition = position+ sf::Vector2f(std::cos(rad-M_PI/2) * 15.0f, std::sin(rad-M_PI/2) * 15.0f);
    return Bullet(bulletPosition, bulletVelocity);
}
