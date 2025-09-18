package com.tariff.tariff_backend.repository;

import java.util.Optional;

import org.springframework.data.jpa.repository.JpaRepository;

import com.tariff.tariff_backend.model.Role;

public interface RoleRepo extends JpaRepository<Role, Integer> {
    Optional<Role> findByName(String name);
}
