#include <SFML/Graphics.hpp>
#include "rocket.hpp"
#include "asteroid.hpp"
#include "bullet.hpp"
#include <vector>
#include <cmath>

const int WIDTH = 1800;
const int HEIGHT = 1000;

void elasticCollision(GameObject &a, GameObject &b, float massA, float massB) {
    sf::Vector2f delta = b.getPosition() - a.getPosition();
    float distance = std::sqrt(delta.x * delta.x + delta.y * delta.y);

    if (distance == 0.0f) return;

    sf::Vector2f normal = delta / distance;
    sf::Vector2f relativeVelocity = b.getVelocity() - a.getVelocity();
    float velocityAlongNormal = relativeVelocity.x * normal.x + relativeVelocity.y * normal.y;

    if (velocityAlongNormal > 0) return;

    float restitution = 1.0f; // Perfectly elastic collision
    float impulse = -(1 + restitution) * velocityAlongNormal / (1 / massA + 1 / massB);

    sf::Vector2f impulseVec = impulse * normal;
    a.setVelocity(a.getVelocity() - impulseVec / massA);
    b.setVelocity(b.getVelocity() + impulseVec / massB);
}

void handleWallCollisions(GameObject &obj, float radius) {
    sf::Vector2f pos = obj.getPosition();
    sf::Vector2f vel = obj.getVelocity();

    if (pos.x - radius <= 0 || pos.x + radius >= WIDTH) {
        vel.x = -0.95*vel.x; // Reverse horizontal velocity
        pos.x = std::clamp(pos.x, radius, static_cast<float>(WIDTH) - radius);
    }
    if (pos.y - radius <= 0 || pos.y + radius >= HEIGHT) {
        vel.y = -0.95*vel.y; // Reverse vertical velocity
        pos.y = std::clamp(pos.y, radius, static_cast<float>(HEIGHT) - radius);
    }

    obj.setPosition(pos);
    obj.setVelocity(vel);
}

void handleCollisions(Rocket &rocket, std::vector<Bullet> &bullets, std::vector<Asteroid> &asteroids) {
    // Handle bullet-asteroid collisions
    for (auto bulletIt = bullets.begin(); bulletIt != bullets.end();) {
        bool hit = false;
        for (auto asteroidIt = asteroids.begin(); asteroidIt != asteroids.end();) {
            sf::Vector2f delta = bulletIt->getPosition() - asteroidIt->getPosition();
            float distance = std::sqrt(delta.x * delta.x + delta.y * delta.y);

            if (distance < asteroidIt->getRadius()) {
                elasticCollision(*bulletIt, *asteroidIt, 0.1f, asteroidIt->getMass()); // Elastic collision
                hit = true;
                break;
            } else {
                ++asteroidIt;
            }
        }
        if (hit) {
            ++bulletIt;
        } else {
            ++bulletIt;
        }
    }

    // Handle rocket-asteroid collisions
    for (auto &asteroid : asteroids) {
        sf::Vector2f delta = rocket.getPosition() - asteroid.getPosition();
        float distance = std::sqrt(delta.x * delta.x + delta.y * delta.y);

        if (distance < asteroid.getRadius() + 10.0f) { // Rocket radius ~10
            elasticCollision(rocket, asteroid, 1.0f, asteroid.getMass());
        }
    }

    // Handle asteroid-asteroid collisions
    for (size_t i = 0; i < asteroids.size(); ++i) {
        for (size_t j = i + 1; j < asteroids.size(); ++j) {
            elasticCollision(asteroids[i], asteroids[j], asteroids[i].getMass(), asteroids[j].getMass());
        }
    }
}

int main() {
    sf::RenderWindow window(sf::VideoMode(WIDTH, HEIGHT), "Space Force");
    Rocket rocket({WIDTH*0.0f+40.0f, HEIGHT / 2.0f});

    // Spawn initial asteroids
    std::vector<Asteroid> asteroids = {
        Asteroid({900, 500}, {0, 0}, 400),
    };

    std::vector<Bullet> bullets;

    sf::Clock clock;

    while (window.isOpen()) {
        float dt = clock.restart().asSeconds();

        // Handle events
        sf::Event event;
        while (window.pollEvent(event)) {
            if (event.type == sf::Event::Closed) window.close();
        }

        // Handle input
        if (sf::Keyboard::isKeyPressed(sf::Keyboard::W)) rocket.applyThrust(dt, true);  // Forward thrust
        if (sf::Keyboard::isKeyPressed(sf::Keyboard::S)) rocket.applyThrust(dt, false); // Backward thrust
        if (sf::Keyboard::isKeyPressed(sf::Keyboard::A)) rocket.applyRotationThrust(dt, false); // Counter-clockwise
        if (sf::Keyboard::isKeyPressed(sf::Keyboard::D)) rocket.applyRotationThrust(dt, true);  // Clockwise
        if (sf::Keyboard::isKeyPressed(sf::Keyboard::Space)) bullets.push_back(rocket.shoot()); // Shoot

        // Update game objects
        rocket.update(dt);
        for (auto &bullet : bullets) bullet.update(dt);
        for (auto &asteroid : asteroids) asteroid.update(dt);

        // Handle wall collisions
        handleWallCollisions(rocket, 10.0f); // Rocket radius ~10
        for (auto &bullet : bullets) handleWallCollisions(bullet, 3.0f); // Bullet radius ~3
        for (auto &asteroid : asteroids) handleWallCollisions(asteroid, asteroid.getRadius());

        // Remove expired bullets
        bullets.erase(std::remove_if(bullets.begin(), bullets.end(),
                                     [](const Bullet &b) { return b.isExpired(); }),
                      bullets.end());

        // Handle collisions
        handleCollisions(rocket, bullets, asteroids);

        // Render everything
        window.clear(sf::Color::Black);
        rocket.draw(window);
        for (const auto &bullet : bullets) bullet.draw(window);
        for (const auto &asteroid : asteroids) asteroid.draw(window);
        window.display();
    }

    return 0;
}
