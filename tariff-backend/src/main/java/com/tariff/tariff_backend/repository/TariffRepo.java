package com.tariff.tariff_backend.repository;

import java.util.List;

import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.JpaSpecificationExecutor;

import com.tariff.tariff_backend.model.tariffs_old.Tariff;

// interfaces with jparepo to allow you to use their CRUD methods on your own class (Tariff)
public interface TariffRepo extends JpaRepository<Tariff, Integer>, JpaSpecificationExecutor<Tariff>{
    List<Tariff> findByHts8(Integer hts8);
    
    Page<Tariff> findByHts8(Integer hts8, Pageable pageable); //Pages return both the data and metadata, metadata helps the frontend to know if there are more results
    
    Page<Tariff> findByBriefDescriptionContainingIgnoreCase(String q, Pageable pageable); 
}
