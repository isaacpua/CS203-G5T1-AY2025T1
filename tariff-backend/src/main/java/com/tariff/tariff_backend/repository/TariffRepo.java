package com.tariff.tariff_backend.repository;

import java.util.List;

import org.springframework.data.jpa.repository.JpaRepository;

import com.tariff.tariff_backend.model.Tariff;

// interfaces with jparepo to allow you to use their CRUD methods on your own class (Tariff)
public interface TariffRepo extends JpaRepository<Tariff, Integer>{
    List<Tariff> findByHts8(Integer hts8);
}
