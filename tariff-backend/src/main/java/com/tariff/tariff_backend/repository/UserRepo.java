package com.tariff.tariff_backend.repository;

import java.util.Optional;
import java.util.UUID;

import org.springframework.data.jpa.repository.JpaRepository;

import com.tariff.tariff_backend.model.User;


public interface UserRepo extends JpaRepository<User, UUID> {
    Optional<User> findByUsername(String username);
}
