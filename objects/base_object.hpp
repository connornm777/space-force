#ifndef BASE_OBJECT_HPP
#define BASE_OBJECT_HPP

#include <SFML/Graphics.hpp>

class GameObject {
protected:
    sf::Vector2f position;
    sf::Vector2f velocity;

public:
    GameObject(sf::Vector2f pos, sf::Vector2f vel) : position(pos), velocity(vel) {}
    virtual ~GameObject() = default;

    virtual void update(float dt) = 0;
    virtual void draw(sf::RenderWindow &window) const = 0;

    sf::Vector2f getPosition() const { return position; }
    void setPosition(const sf::Vector2f &pos) { position = pos; }

    sf::Vector2f getVelocity() const { return velocity; }
    void setVelocity(const sf::Vector2f &vel) { velocity = vel; }
};

#endif
