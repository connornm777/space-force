#ifndef BULLET_HPP
#define BULLET_HPP

#include "base_object.hpp"

class Bullet : public GameObject {
private:
    float lifetime;
    float timeAlive;
    sf::CircleShape shape;

public:
    Bullet(sf::Vector2f pos, sf::Vector2f vel);
    void update(float dt) override;
    void draw(sf::RenderWindow &window) const override;

    bool isExpired() const;
};

#endif
