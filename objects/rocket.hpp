#ifndef ROCKET_HPP
#define ROCKET_HPP

#include "base_object.hpp"
#include "bullet.hpp"
#include <cmath>
#include <vector>

class Rocket : public GameObject {
private:
    sf::ConvexShape shape;
    float angle;
    float angularVelocity;

    const float thrustPower = 1000.0f;
    const float rotationThrust = 500.0f;
    bool thrusting; // Tracks whether the rocket is applying thrust

public:
    Rocket(sf::Vector2f pos);
    void update(float dt) override;
    void draw(sf::RenderWindow &window) const override;

    void applyThrust(float dt, bool forward);
    void applyRotationThrust(float dt, bool clockwise);
    void reset();
    Bullet shoot() const;

    bool isThrusting() const { return thrusting; } // For flame animation
};

#endif
