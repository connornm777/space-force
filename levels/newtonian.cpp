#include "newtonian.hpp"

void NewtonianLevel::draw(sf::RenderWindow &window) {
    sf::CircleShape blackHole(blackHoleRadius);
    blackHole.setFillColor(sf::Color::Black);
    blackHole.setOrigin(blackHoleRadius, blackHoleRadius);
    blackHole.setPosition(window.getSize().x / 2.0f, window.getSize().y / 2.0f);
    window.draw(blackHole);
}
