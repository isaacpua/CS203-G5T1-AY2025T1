package com.tariff.tariff_backend.repository;

import java.util.List;

import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.JpaSpecificationExecutor;

import com.tariff.tariff_backend.model.Tariff;

// interfaces with jparepo to allow you to use their CRUD methods on your own class (Tariff)
public interface TariffRepo extends JpaRepository<Tariff, Integer>, JpaSpecificationExecutor<Tariff>{
    List<Tariff> findByTariffid(Integer tariffid);
    Page<Tariff> findByTariffid(Integer tariffid, Pageable pageable);
    Page<Tariff> findByDescriptionwcountryContainingIgnoreCase(String q, Pageable pageable);
}
